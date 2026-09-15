"""Safaricom source config.

Researched directly against the live site (fetched 2026-08-11), then further
confirmed against genuinely live-rendered output on 2026-08-12/13 (via
diagnostic runs against the real page), which is worth distinguishing before
touching the selectors below: some of this is research, and some of it is
now directly verified.

Confirmed via research (2026-08-11):
- https://www.safaricom.co.ke/careers/ is server rendered (a Joomla site) and
  surfaces one featured role, too short a snippet to count as a full posting.
- The full requisition list lives on a separate Oracle Cloud HCM "Candidate
  Experience" portal (egjd.fa.us6.oraclecloud.com), confirmed to be a
  JavaScript-rendered single page app (a plain fetch there returns only meta
  tags). needs_js=True is not a guess.

Confirmed via live output (2026-08-12), list page:
- Job links are real <a href="...CX/job/<id>"> tags, but each is EMPTY (no
  text between open and close tag). The visible title lives in a separate
  element tied to the link via aria-labelledby="<id>", a real accessibility
  pattern. That element's full text runs title, location, and posting date
  together with no separators, e.g. "Engineer - Managed Security
  SolutionsLocationsKenyaPosting Date11/08/2026", sometimes with "Trending"
  appended. Confirmed identically across multiple real listings.
  _split_card_text() parses that specific, consistent shape.
- The framework in use is Knockout.js (visible in data-bind="click: () =>
  openJobPreview(job.id)" attributes).
- The live list genuinely changes between runs (4 jobs on one run, 2 on a
  later one, 3 on another), which is expected, not a bug: it's a real, live
  job board.

Confirmed via a real detail page, job/1410 (2026-08-12/13):
- The description lives in a div whose data-bind is exactly
  html: pageData().job.description, class="job-details__description-content",
  containing real <p> paragraphs. Directly confirmed and extracted below.
- "Job Info" rows (Apply Before, Job Identification, and presumably others)
  render as sibling pairs: span.job-meta__title holding the label, followed
  by a sibling span.job-meta__subitem holding the value. Directly confirmed
  for "Apply Before" specifically, and used below for application_deadline.
  The first version of this file walked that sibling relationship via a
  parent.children list, which was wrong: real selectolax Node objects have
  no .children attribute at all (confirmed by installing the actual library
  and inspecting one directly, after this exact assumption caused a real
  AttributeError on a live run against Elvis's machine). The real API is
  .next / .prev / .parent / .child, a linked-list style, not a list-based
  one, and _find_meta_value() below now uses that, verified against the
  real installed library, not assumed.
- Responsibilities and qualifications: pageData().job.responsibilities and
  pageData().job.qualifications are confirmed to exist (visible in
  <!-- ko if: --> conditionals guarding their sections), but the research
  trail ran out before their own content div's class name was confirmed the
  way description's was. Deliberately left unextracted here rather than
  assumed from the naming pattern alone; parse_detail() returns None for
  both until that's actually seen.
- selectors_verified is still False for exactly that reason: description and
  the deadline are solid, two fields are still open.
"""
import re
from datetime import date, datetime

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
    back apart using the exact pattern confirmed against real cards. Falls
    back to treating the whole string as the title if it doesn't match that
    pattern, so a future markup change degrades to "an unparsed title"
    rather than breaking outright.
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


def _find_meta_value(tree: HTMLParser, label: str) -> str | None:
    """"Job Info" fields render as sibling span pairs: span.job-meta__title
    holding the label text, immediately followed by a sibling
    span.job-meta__subitem holding the value. Confirmed directly for
    "Apply Before" against a real detail page.

    Walks siblings via .next rather than a parent.children list: real
    selectolax Node objects have no .children attribute at all (confirmed
    directly against the installed library after this exact assumption
    caused a real AttributeError on a live run), only .next / .prev / .parent
    / .child, a linked-list style API, not the list-based one this originally
    assumed.
    """
    for title_node in tree.css("span[class='job-meta__title']"):
        if title_node.text(strip=True) != label:
            continue
        sibling = title_node.next
        while sibling is not None:
            if sibling.tag == "span" and sibling.attributes.get("class") == "job-meta__subitem":
                return sibling.text(strip=True)
            sibling = sibling.next
        return None
    return None


def _parse_deadline(raw: str | None) -> date | None:
    """"Apply Before" values look like "17/08/2026, 00:00": day/month/year
    (confirmed by validity: 17 as a month would be invalid), a comma, then a
    time this pipeline doesn't need. Only the date part is used.
    """
    if not raw:
        return None
    date_part = raw.split(",")[0].strip()
    try:
        return datetime.strptime(date_part, "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_detail(html: str) -> dict:
    """Parse a job's detail page into description, requirements,
    responsibilities, and the application deadline.

    Description and the deadline are extracted for real, against confirmed
    selectors. Requirements and responsibilities return None deliberately:
    the fields are confirmed to exist in the underlying data
    (pageData().job.qualifications / .responsibilities), but their specific
    content div wasn't confirmed the way description's was, so guessing at
    it here would repeat exactly the mistake this file has already made
    once (the empty-title bug) and had to fix.
    """
    tree = HTMLParser(html)

    description_node = tree.css_first("div[class='job-details__description-content']")
    description = description_node.text(strip=True) if description_node else None

    application_deadline = _parse_deadline(_find_meta_value(tree, "Apply Before"))

    return {
        "description": description,
        "requirements": None,
        "responsibilities": None,
        "application_deadline": application_deadline,
    }
