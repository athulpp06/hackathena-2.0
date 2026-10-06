"""
scraper.py - SSRF-hardened web scraper for LeakedIn.

Security protections:
  - DNS resolution with private IP range blocking (RFC 1918, loopback, link-local, metadata)
  - Redirect following with destination IP re-validation
  - Only http/https schemes allowed
  - Capped response size (2 MB) and redirect count (3)
  - Reasonable timeouts (10s connect, 15s read)
  - Graceful failure with user-friendly messages
"""

import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = 2 * 1024 * 1024   # 2 MB
MAX_REDIRECTS = 3
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 15

_SCRAPER_UA = (
    "Mozilla/5.0 (compatible; LeakedIn-Scraper/1.0; +https://github.com/leakedin)"
)

# IP ranges that are never permitted as scraping destinations
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("::1/128"),             # IPv6 loopback
    ipaddress.ip_network("169.254.0.0/16"),      # link-local / AWS metadata
    ipaddress.ip_network("fd00::/8"),            # IPv6 ULA
    ipaddress.ip_network("100.64.0.0/10"),       # shared address space
    ipaddress.ip_network("0.0.0.0/8"),           # this network
]


# --- Exceptions for Structured Error Handling ---
class ScrapeError(Exception):
    """Base exception for scraping failures."""


class BlockedURLError(ScrapeError, ValueError):
    """Raised when a URL is blocked due to SSRF safeguards or restricted domains."""


class ScrapingNotAllowedError(ScrapeError):
    """Raised when a website blocks automated scraping."""


class FetchError(ScrapeError):
    """Raised when network fetch fails (timeout, connection error, etc.)."""


def _is_private_ip(host: str) -> bool:
    """Return True if host resolves to a private/internal IP address."""
    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip_str = info[4][0]
            ip = ipaddress.ip_address(ip_str)
            if any(ip in net for net in _PRIVATE_NETWORKS):
                return True
        return False
    except socket.gaierror:
        return True   # Treat DNS failure as blocked


def _validate_url(url: str) -> str:
    """
    Validate URL scheme and destination IP.
    Returns the URL if safe, raises BlockedURLError otherwise.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise BlockedURLError(f"Only http and https URLs are supported (got: '{parsed.scheme}').")

    host = parsed.hostname
    if not host:
        raise BlockedURLError("Could not parse hostname from URL.")

    # Block raw IP-address URLs
    try:
        ip = ipaddress.ip_address(host)
        if any(ip in net for net in _PRIVATE_NETWORKS):
            raise BlockedURLError(f"Requests to internal IP addresses are not allowed ({host}).")
    except ValueError as exc:
        if "not allowed" in str(exc):
            raise BlockedURLError(str(exc)) from exc

    # Block DNS resolving to private IP
    if _is_private_ip(host):
        raise BlockedURLError(f"Blocked URL: resolves to a private or internal network address ({host}).")

    return url


def scrape_job_url(url: str) -> str:
    """
    Scrape text content from a job posting URL safely.

    Returns:
        Cleaned text extracted from the page.

    Raises:
        BlockedURLError: SSRF or private IP attempt.
        ScrapingNotAllowedError: HTTP 401/403/bot-blocked.
        ScrapeError: General fetch failure or insufficient content.
    """
    safe_url = _validate_url(url.strip())
    parsed = urlparse(safe_url)

    if parsed.hostname and "linkedin.com" in parsed.hostname.lower():
        raise ScrapingNotAllowedError(
            "This website blocks automated scanning (LinkedIn bot protection). "
            "Please copy and paste the job posting text directly into the Text tab."
        )

    session = requests.Session()
    session.headers.update({
        "User-Agent": _SCRAPER_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })

    current_url = safe_url
    response = None

    # Follow redirects manually to re-validate destination IP on each hop
    for _ in range(MAX_REDIRECTS + 1):
        try:
            response = session.get(
                current_url,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=False,
                stream=True,
            )
        except requests.exceptions.Timeout as exc:
            raise FetchError("Connection timed out while fetching the URL.") from exc
        except requests.exceptions.RequestException as exc:
            raise FetchError(f"Failed to fetch URL: {exc}") from exc

        if response.status_code in (301, 302, 303, 307, 308):
            next_url = response.headers.get("Location")
            if not next_url:
                break
            current_url = _validate_url(next_url)
            continue
        break

    if response is None:
        raise FetchError("Failed to receive a response from the server.")

    # Status checks
    if response.status_code in (401, 403):
        raise ScrapingNotAllowedError(
            f"This website blocks automated scanning (HTTP {response.status_code}). "
            "Please copy and paste the job posting text directly into the Text tab."
        )

    if response.status_code != 200:
        raise FetchError(
            f"The server returned an error (HTTP {response.status_code}). "
            "Please check the URL or paste the job description text directly."
        )

    # Read content up to size limit
    content = b""
    for chunk in response.iter_content(chunk_size=65536):
        content += chunk
        if len(content) > MAX_RESPONSE_BYTES:
            logger.warning("Scraped response exceeded limit; truncating to 2 MB.")
            break

    # Extract text from HTML
    encoding = response.encoding or "utf-8"
    try:
        html = content.decode(encoding, errors="replace")
    except Exception:
        html = content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    # Prefer main / article / job-specific containers if present
    content_root = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"job|posting|description|content", re.I))
        or soup.find(class_=re.compile(r"job|posting|description|content", re.I))
        or soup.body
        or soup
    )

    lines = (line.strip() for line in content_root.get_text().splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = "\n".join(chunk for chunk in chunks if chunk)

    if not cleaned_text.strip():
        raise ScrapeError(
            "Could not extract sufficient text from this URL. "
            "The page may require JavaScript or login. "
            "Please copy and paste the text directly into the Text tab."
        )

    return cleaned_text
