"""Safaricom source config.

Researched directly against the live site (fetched 2026-08-11), then further
confirmed against genuinely live-rendered output on 2026-08-12 (via a
diagnostic run against the real page), which is worth distinguishing before
touching the selectors below: some of this is research, and some of it is now
directly verified.

Confirmed via research (2026-08-11):
- https://www.safaricom.co.ke/careers/ is server rendered (a Joomla site) and
  surfaces one featured role, too short a snippet to count as a full posting.
- The full requisition list lives on a separate Oracle Cloud HCM "Candidate
  Experience" portal (egjd.fa.us6.oraclecloud.com), confirmed to be a
  JavaScript-rendered single page app (a plain fetch there returns only meta
  tags). needs_js=True is not a guess.

Confirmed via live output (2026-08-12), genuinely different from a guess:
- Job links are real <a href="...CX/job/<id>"> tags. There are exactly 4 on
  the live requisitions page, matching the "4 open jobs" shown on the page.
- Each of those <a> tags is EMPTY (no text between the open and close tag).
  The visible title lives in a separate element elsewhere in the DOM, tied to
  the link only via aria-labelledby="<id>", a legitimate accessibility
  pattern, not a shortcut. parse_list() below reads that element for the
  title now, which is exactly what account for the very first version of this
  function returning zero results against a page that genuinely has 4 jobs on
  it: it was checking the link's own (empty) text and giving up.
- That element isn't just the title, though: it's a card container, and its
  full text runs title, location, and posting date together with no
  separators, e.g. "Engineer - Managed Security SolutionsLocationsKenya
  Posting Date11/08/2026", sometimes with "Trending" appended. Confirmed
  identically across all 4 real listings, so _split_card_text() below parses
  that specific, consistent shape rather than guessing at a general one.
- The framework in use is Knockout.js (visible in data-bind="click: () =>
  openJobPreview(job.id)" attributes), not React or Angular as originally
  assumed possible.

Still not confirmed:
- The detail page (what parse_detail needs) hasn't been seen at all yet.
  selectors_verified stays False until that happens too.
"""
import re

from selectolax.parser import HTMLParser

from scraper.sources.base import SourceConfig

CONFIG = SourceConfig(
    company_slug="safaricom",
    company_name="Safaricom PLC",
    list_url="https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/requisitions",
    needs_js=True,
    selectors_verified=False,
)

_CARD_TEXT_RE = re.compile(
    r"^(?P<title>.+?)Locations(?P<location>.+?)Posting Date(?P<date>\d{2}/\d{2}/\d{4})(?P<trending>Trending)?$"
)


def _split_card_text(text: str) -> dict:
    """Oracle HCM's job cards concatenate title, location, and posting date
    into one block of text with no separators between them. This splits that
    back apart using the exact pattern confirmed against 4 real cards. Falls
    back to treating the whole string as the title if it doesn't match that
    pattern, so a future markup change (or a different source reusing this
    helper) degrades to "an unparsed title" rather than breaking outright.
    """
    match = _CARD_TEXT_RE.match(text)
    if not match:
        return {"title": text, "location": None, "is_hybrid": False, "is_remote": False}

    title = match.group("title").strip()
    location_raw = match.group("location").strip()
    is_hybrid = "(hybrid)" in location_raw.lower()
    is_remote = "(remote)" in location_raw.lower()
    location = re.sub(r"\([^)]*\)", "", location_raw).strip() or None

    return {"title": title, "location": location, "is_hybrid": is_hybrid, "is_remote": is_remote}


def parse_list(html: str) -> list[dict]:
    """Parse the (JavaScript-rendered) Oracle HCM requisitions page into a
    list of {title, detail_url, county, is_hybrid, is_remote} records.

    The job link's own text is tried first, for forward compatibility if a
    future markup change ever puts the title back inside the anchor. The
    fallback, reading the element referenced by aria-labelledby, is what the
    live page actually needs today, and that text then gets split by
    _split_card_text() since it's a whole card's worth of concatenated text,
    not just a title.
    """
    tree = HTMLParser(html)
    results = []
    for link in tree.css("a[href*='/job/']"):
        href = link.attributes.get("href")
        if not href:
            continue

        raw_text = link.text(strip=True)
        if not raw_text:
            label_id = link.attributes.get("aria-labelledby")
            if label_id:
                label_node = tree.css_first(f"[id='{label_id}']")
                if label_node:
                    raw_text = label_node.text(strip=True)

        if not raw_text:
            continue

        parsed = _split_card_text(raw_text)
        if not parsed["title"]:
            continue

        results.append({
            "title": parsed["title"],
            "detail_url": href,
            "county": parsed["location"],
            "is_hybrid": parsed["is_hybrid"],
            "is_remote": parsed["is_remote"],
        })
    return results


def parse_detail(html: str) -> dict:
    """Parse a single job's detail page into the full description, requirements,
    and responsibilities.

    Not implemented. One specific detail URL was visible during research
    (.../CX/job/1401) but fetching it directly was blocked: this environment's
    fetch tool only allows URLs that came back from an actual search or fetch
    result, not ones merely seen as link text inside another page. Getting a
    working version of this function needs either a direct detail-page URL to
    research properly, or a live tuning pass once Playwright is wired in and
    the page can actually be rendered and inspected.
    """
    raise NotImplementedError(
        "Safaricom detail-page parsing needs research against a real detail "
        "page before it can be written; see this function's docstring."
    )
