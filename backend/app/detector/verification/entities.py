"""
entities.py - Entity extraction from job posting text.

Extracts: emails, phone numbers, URLs, UPI IDs, Telegram/WhatsApp handles, bank account patterns.
"""

import re

# Regex patterns for entity extraction
_EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.[a-z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s]+|(?:www\.)[^\s]+", re.IGNORECASE)
_UPI_RE = re.compile(r"[\w.\-]+@(?:okaxis|okhdfcbank|okicici|oksbi|ybl|upi|paytm|ibl)", re.IGNORECASE)
_TELEGRAM_RE = re.compile(r"(?:t\.me/|telegram\.me/|@)[\w]{5,}", re.IGNORECASE)
_WHATSAPP_RE = re.compile(r"(?:wa\.me/|whatsapp\.com/|contact.*whatsapp.*?)(?:\+?91)?[6-9]\d{9}", re.IGNORECASE)
_BANK_ACCOUNT_RE = re.compile(r"\b\d{9,18}\b(?=.*(?:account|acct|bank|IFSC))", re.IGNORECASE | re.DOTALL)


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract structured entities from text.

    Returns a dict with keys: emails, phones, urls, upi_ids, telegram_handles, bank_accounts.
    """
    emails = list(set(_EMAIL_RE.findall(text)))
    phones = list(set(_PHONE_RE.findall(text)))
    urls = list(set(_URL_RE.findall(text)))
    upi_ids = list(set(_UPI_RE.findall(text)))
    telegram = list(set(_TELEGRAM_RE.findall(text)))
    bank_accounts = list(set(_BANK_ACCOUNT_RE.findall(text)))

    return {
        "emails": emails,
        "phones": phones,
        "urls": urls,
        "upi_ids": upi_ids,
        "telegram_handles": telegram,
        "bank_accounts": bank_accounts,
    }


def get_domains_from_urls(urls: list[str]) -> list[str]:
    """Extract unique domain names from a list of URLs."""
    domain_re = re.compile(r"(?:https?://)?(?:www\.)?([^/\s?#]+)", re.IGNORECASE)
    domains = []
    for url in urls:
        m = domain_re.match(url)
        if m:
            domains.append(m.group(1).lower())
    return list(set(domains))
