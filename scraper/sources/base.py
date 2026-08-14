"""Declarative metadata for one scrape source.

Adding a new organization whose page is regular enough to fit this shape means
adding a new SourceConfig and a parse() function in its own module, not new
pipeline code. See SRS section 10 for the reasoning.

The actual parsing logic is NOT part of this dataclass on purpose: every site's
markup is different enough that trying to force a shared, generic parser would
just turn into a pile of special cases hidden inside one function. Each source
module owns its own parse().
"""
from dataclasses import dataclass


@dataclass
class SourceConfig:
    company_slug: str
    company_name: str
    list_url: str
    needs_js: bool = False
    # Set True once this source's parser has been checked against the real,
    # live-rendered page (not just researched from fetched/extracted content).
    # See scraper/sources/safaricom.py for what that distinction means in
    # practice and why it matters.
    selectors_verified: bool = False
