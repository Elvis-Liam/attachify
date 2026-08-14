"""Builders for JSON-LD structured data blocks used across the public pages.

Kept separate from app/web/pages.py so the escaping and schema-shape logic has one
home. The escaping matters more than it looks: once the scraper is pulling real
content from external sites, that text ends up inside a <script> tag, and without
escaping "</" sequences a value like a company description containing "</script>"
could break the page. Not a risk with today's hand-written seed data, but the kind
of thing worth getting right before real scraped content flows through it.
"""
import json
from typing import Any

from app.models.company import Company
from app.models.opportunity import Opportunity

EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "attachment": "INTERN",
    "internship": "INTERN",
    "apprenticeship": "INTERN",
    "graduate_program": "FULL_TIME",
}


def _safe_json(data: dict[str, Any]) -> str:
    """Serialize to JSON that is safe to embed inside a <script> tag."""
    return json.dumps(data).replace("</", "<\\/")


def job_posting_json_ld(opportunity: Opportunity, page_url: str) -> str:
    """Build the JobPosting JSON-LD block for a single opportunity detail page.

    Covers Google's five required properties (title, description, datePosted,
    hiringOrganization, jobLocation) plus the recommended ones we have real data
    for (employmentType, validThrough, baseSalary). See SRS section 13.
    """
    description_parts = [opportunity.description]
    if opportunity.requirements:
        description_parts.append(f"Requirements: {opportunity.requirements}")
    if opportunity.responsibilities:
        description_parts.append(f"Responsibilities: {opportunity.responsibilities}")

    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": opportunity.title,
        "description": " ".join(description_parts),
        "datePosted": opportunity.created_at.date().isoformat(),
        "hiringOrganization": {
            "@type": "Organization",
            "name": opportunity.company.name,
        },
        "employmentType": EMPLOYMENT_TYPE_MAP.get(opportunity.type, "OTHER"),
        "url": page_url,
        "identifier": {
            "@type": "PropertyValue",
            "name": opportunity.company.name,
            "value": str(opportunity.id),
        },
    }

    if opportunity.company.website:
        data["hiringOrganization"]["sameAs"] = opportunity.company.website

    if opportunity.is_remote:
        data["jobLocationType"] = "TELECOMMUTE"
        data["applicantLocationRequirements"] = {"@type": "Country", "name": "Kenya"}
    else:
        data["jobLocation"] = {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": opportunity.town or opportunity.county or "Kenya",
                "addressRegion": opportunity.county or "Kenya",
                "addressCountry": "KE",
            },
        }

    if opportunity.application_deadline:
        data["validThrough"] = opportunity.application_deadline.isoformat()

    if opportunity.is_paid and opportunity.stipend_amount:
        data["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": "KES",
            "value": {
                "@type": "QuantitativeValue",
                "value": float(opportunity.stipend_amount),
                "unitText": "MONTH",
            },
        }

    return _safe_json(data)
