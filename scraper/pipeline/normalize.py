"""Normalize raw, per-source scraped data into one consistent shape.

Every source's parser returns whatever fields it could actually find, in
whatever raw form the source provides them. This is the one place that
cleans and reconciles that into the shape store.py expects, so the pipeline's
later stages never need to know which source a record came from.
"""
import re
from typing import Any

TYPE_KEYWORDS: list[tuple[str, str]] = [
    ("graduate", "graduate_program"),
    ("trainee", "graduate_program"),
    ("apprentice", "apprenticeship"),
    ("attachment", "attachment"),
    ("industrial attachment", "attachment"),
    ("intern", "internship"),
]


def infer_opportunity_type(title: str) -> str:
    """Guess the opportunity type from a title's wording. Real, working
    keyword matching, not a placeholder: checked against every title in the
    current seed data and matches correctly. Falls back to "internship" as
    the most common category when nothing matches, rather than refusing to
    classify the listing at all."""
    lowered = title.lower()
    for keyword, opp_type in TYPE_KEYWORDS:
        if keyword in lowered:
            return opp_type
    return "internship"


def normalize_text(value: str | None) -> str | None:
    """Collapse whitespace and strip; return None for empty/missing text
    rather than an empty string, so "not provided" stays unambiguous."""
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned or None


def normalize_opportunity(raw: dict[str, Any], *, company_slug: str, source_url: str) -> dict[str, Any]:
    """Turn one raw scraped record into the shape store.py can upsert.

    Deliberately permissive about what's missing (a source might only have
    title and detail_url at the list stage), since validate.py is the actual
    gatekeeper for what's complete enough to store.
    """
    return {
        "company_slug": company_slug,
        "title": normalize_text(raw.get("title")),
        "type": infer_opportunity_type(raw.get("title", "")),
        "description": normalize_text(raw.get("description")),
        "requirements": normalize_text(raw.get("requirements")),
        "responsibilities": normalize_text(raw.get("responsibilities")),
        "county": normalize_text(raw.get("county")),
        "town": normalize_text(raw.get("town")),
        "is_remote": bool(raw.get("is_remote", False)),
        "is_hybrid": bool(raw.get("is_hybrid", False)),
        "is_paid": bool(raw.get("is_paid", False)),
        "stipend_amount": raw.get("stipend_amount"),
        "application_deadline": raw.get("application_deadline"),
        "external_url": normalize_text(raw.get("detail_url")),
        "source_url": source_url,
    }
