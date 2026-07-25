"""
q2_knowledge_base/cleaner.py — Data cleaning, dedup, normalization, PII detection

Handles the assessment's data quality requirements:
  - Remove nav text, headers, footers, repeated sections
  - Deduplicate near-duplicate content
  - Standardize terminology, headings, dates
  - Identify and flag PII (regex-based, no heavy deps)
"""

import re
import hashlib
from typing import Optional

from shared.logger import get_logger

log = get_logger("q2.cleaner")


# ── PII patterns (lightweight regex, no presidio/spacy needed) ──
PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone_india": re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"),
    "phone_intl": re.compile(r"\b\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
    "aadhaar": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),  # Indian Aadhaar
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),  # Indian PAN
}

# ── Boilerplate patterns to strip from scraped content ──────────
BOILERPLATE_PATTERNS = [
    re.compile(r"(?i)^(copyright|©|all rights reserved).*$", re.MULTILINE),
    re.compile(r"(?i)^(privacy policy|terms of service|cookie policy).*$", re.MULTILINE),
    re.compile(r"(?i)^(subscribe|sign up|newsletter|follow us).*$", re.MULTILINE),
    re.compile(r"(?i)^(home|about|contact|menu|navigation|sitemap)\s*$", re.MULTILINE),
    re.compile(r"(?i)^(share|tweet|facebook|linkedin|instagram)\s*$", re.MULTILINE),
    re.compile(r"\[.*?\]\(javascript:.*?\)", re.MULTILINE),  # JS links in markdown
]

# ── Health insurance terminology standardization ────────────────
# Maps variant spellings/abbreviations to canonical forms
TERMINOLOGY_MAP = {
    r"\bhealth\s+ins\b": "health insurance",
    r"\bpre-existing\s+disease\b": "pre-existing condition",
    r"\bPED\b": "pre-existing condition",
    r"\bsum\s+assured\b": "sum insured",
    r"\bSA\b": "sum insured",
    r"\bSI\b": "sum insured",
    r"\bno\s+claim\s+bonus\b": "no-claim bonus",
    r"\bNCB\b": "no-claim bonus",
    r"\bTPA\b": "third-party administrator",
    r"\bOPD\b": "outpatient department",
    r"\bIPD\b": "inpatient department",
    r"\bcopay\b": "co-payment",
    r"\bco\s*-?\s*pay\b": "co-payment",
    r"\bday\s+care\b": "day-care procedure",
}


def detect_pii(text: str) -> dict:
    """
    Scan text for PII patterns and return findings.

    Returns:
        Dict with pii_detected (bool) and list of matched types.
        Does NOT return the actual PII values — only flags presence.
    """
    found_types = []
    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            found_types.append(pii_type)

    return {
        "pii_detected": len(found_types) > 0,
        "pii_types": found_types,
    }


def redact_pii(text: str) -> str:
    """
    Replace detected PII with redaction markers.

    Redaction format: [REDACTED_TYPE] (e.g., [REDACTED_EMAIL])
    This preserves document structure while protecting sensitive data.
    """
    for pii_type, pattern in PII_PATTERNS.items():
        text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", text)
    return text


def remove_boilerplate(text: str) -> str:
    """
    Strip common website boilerplate from scraped markdown.

    Targets: copyright notices, nav links, social sharing buttons,
    newsletter prompts, and JS-based links.
    """
    for pattern in BOILERPLATE_PATTERNS:
        text = pattern.sub("", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace while preserving paragraph breaks."""
    # Collapse 3+ newlines to 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces to single
    text = re.sub(r" {2,}", " ", text)
    # Strip trailing whitespace per line
    text = re.sub(r" +\n", "\n", text)
    return text.strip()


def standardize_terminology(text: str) -> str:
    """
    Replace variant spellings and abbreviations with canonical terms.

    Specific to health insurance domain per assessment use case.
    Case-insensitive matching with word boundaries.
    """
    for pattern, replacement in TERMINOLOGY_MAP.items():
        text = re.compile(pattern, re.IGNORECASE).sub(replacement, text)
    return text


def content_hash(text: str) -> str:
    """
    Generate a content fingerprint for deduplication.

    Uses MD5 on normalized text (lowered, whitespace-collapsed).
    Not cryptographic — just for fast equality checking.
    """
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()


def deduplicate(records: list[dict], content_key: str = "content") -> list[dict]:
    """
    Remove near-duplicate records based on content hash.

    Args:
        records: List of dicts containing content
        content_key: Dict key holding the text to compare

    Returns:
        Deduplicated list (first occurrence kept)
    """
    seen_hashes: set[str] = set()
    unique = []

    for record in records:
        h = content_hash(record.get(content_key, ""))
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(record)
        else:
            log.debug("duplicate_removed", hash=h[:8])

    removed = len(records) - len(unique)
    if removed:
        log.info("dedup_complete", original=len(records), unique=len(unique), removed=removed)

    return unique


def clean_document(raw_content: dict) -> Optional[dict]:
    """
    Full cleaning pipeline for a single scraped document.

    Pipeline: boilerplate removal → whitespace normalization →
    terminology standardization → PII detection + redaction.

    Args:
        raw_content: Output from scraper.scrape_url()

    Returns:
        Cleaned content dict with PII metadata, or None if empty.
    """
    markdown = raw_content.get("markdown", "")
    if not markdown or len(markdown.strip()) < 50:
        log.warning("content_too_short", url=raw_content.get("url", ""))
        return None

    # Step 1: strip website boilerplate
    cleaned = remove_boilerplate(markdown)

    # Step 2: normalize whitespace
    cleaned = normalize_whitespace(cleaned)

    # Step 3: standardize domain terminology
    cleaned = standardize_terminology(cleaned)

    # Step 4: detect PII before redaction (for metadata)
    pii_info = detect_pii(cleaned)

    # Step 5: redact PII in content
    cleaned = redact_pii(cleaned)

    # Reject if cleaning left nothing substantial
    if len(cleaned.strip()) < 30:
        log.warning("content_empty_after_clean", url=raw_content.get("url", ""))
        return None

    return {
        "url": raw_content.get("url", ""),
        "title": raw_content.get("title", ""),
        "content": cleaned,
        "pii_detected": pii_info["pii_detected"],
        "pii_types": pii_info["pii_types"],
        "content_hash": content_hash(cleaned),
    }
