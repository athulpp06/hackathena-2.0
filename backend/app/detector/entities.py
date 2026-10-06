"""
entities.py - Structured entity extractor for Indian recruitment fraud indicators.

Extracts:
- UPI IDs (e.g. agent@okaxis, hr@paytm, jobfee@ybl)
- Indian phone numbers (+91, 10-digit mobile)
- Telegram & WhatsApp handles
- URLs and domains
- Bank account & IFSC references
"""

import re
from typing import Dict, List

_EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.[a-z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s]+|(?:www\.)[^\s]+", re.IGNORECASE)
_UPI_RE = re.compile(r"[\w.\-]+@(?:okaxis|okhdfcbank|okicici|oksbi|ybl|upi|paytm|ibl|gpay|phonepe)", re.IGNORECASE)
_TELEGRAM_RE = re.compile(r"(?:t\.me/|telegram\.me/|@)[\w]{5,}", re.IGNORECASE)
_WHATSAPP_RE = re.compile(r"(?:wa\.me/|whatsapp\.com/|contact.*whatsapp.*?)(?:\+?91)?[6-9]\d{9}", re.IGNORECASE)
_BANK_ACCOUNT_RE = re.compile(r"\b\d{9,18}\b(?=.*(?:account|acct|bank|IFSC))", re.IGNORECASE | re.DOTALL)
_IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.IGNORECASE)


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract structured entities from text.
    Returns unique lists of identifiers found in the input.
    """
    emails = list(dict.fromkeys(_EMAIL_RE.findall(text)))
    phones = list(dict.fromkeys(_PHONE_RE.findall(text)))
    urls = list(dict.fromkeys(_URL_RE.findall(text)))
    upi_ids = list(dict.fromkeys(_UPI_RE.findall(text)))
    telegram = list(dict.fromkeys(_TELEGRAM_RE.findall(text)))
    bank_accounts = list(dict.fromkeys(_BANK_ACCOUNT_RE.findall(text)))
    ifsc_codes = list(dict.fromkeys(_IFSC_RE.findall(text)))

    return {
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "upi_ids": upi_ids,
        "telegram_handles": telegram,
        "bank_accounts": bank_accounts,
        "ifsc_codes": ifsc_codes,
    }


def get_domains_from_urls(urls: List[str]) -> List[str]:
    """Extracts unique domain names from a list of URLs."""
    domain_re = re.compile(r"(?:https?://)?(?:www\.)?([^/\s?#]+)", re.IGNORECASE)
    domains = []
    for url in urls:
        m = domain_re.match(url)
        if m:
            domains.append(m.group(1).lower())
    return list(dict.fromkeys(domains))
