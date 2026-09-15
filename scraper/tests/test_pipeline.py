"""Plain-assertion tests for the scraper pipeline. Run with: python tests/test_pipeline.py

No pytest dependency on purpose, so these run anywhere Python does. Covers what
this environment can actually verify: normalization, validation, and a source
parser's selector logic against synthetic HTML built to match the real pattern
confirmed during research (list-page card structure, and the real detail-page
markup for description and the application deadline). It does not and cannot
cover whether Safaricom's live page still matches that pattern on any given
day, since that needs a live run to find out, and real sites change.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scraper.pipeline.normalize import infer_opportunity_type, normalize_opportunity, normalize_text
from scraper.pipeline.validate import ValidationError, validate_opportunity
from scraper.sources import safaricom
from scraper.sources.safaricom import _split_card_text

passed, failed = 0, 0


def check(description: str, condition: bool) -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  ok: {description}")
    else:
        failed += 1
        print(f"  FAIL: {description}")


print("normalize_text")
check("collapses internal whitespace", normalize_text("hello   world\n\ttest") == "hello world test")
check("strips leading and trailing space", normalize_text("  hi  ") == "hi")
check("empty string becomes None", normalize_text("") is None)
check("None stays None", normalize_text(None) is None)

print("infer_opportunity_type")
check("'Software Engineering Internship' -> internship", infer_opportunity_type("Software Engineering Internship") == "internship")
check("'Finance Graduate Trainee Program' -> graduate_program", infer_opportunity_type("Finance Graduate Trainee Program") == "graduate_program")
check("'Industrial Attachment: Mechanical' -> attachment", infer_opportunity_type("Industrial Attachment: Mechanical Engineering") == "attachment")
check("'Software Engineering Apprenticeship' -> apprenticeship", infer_opportunity_type("Software Engineering Apprenticeship") == "apprenticeship")
check("unrecognized title falls back to internship", infer_opportunity_type("Something Unusual") == "internship")

print("validate_opportunity")
good_record = {
    "title": "Software Engineering Internship",
    "description": "A description that is definitely longer than twenty characters.",
    "company_slug": "safaricom",
    "source_url": "https://example.com/job/1",
}
try:
    validate_opportunity(good_record)
    check("a complete record passes validation", True)
except ValidationError:
    check("a complete record passes validation", False)

try:
    validate_opportunity({**good_record, "description": "too short"})
    check("a too-short description is rejected", False)
except ValidationError as exc:
    check("a too-short description is rejected", "too short" in exc.reason)

try:
    validate_opportunity({**good_record, "title": None})
    check("a missing title is rejected", False)
except ValidationError as exc:
    check("a missing title is rejected", "title" in exc.reason)

try:
    validate_opportunity({**good_record, "description": "This looks like a real sentence but it just trails off..."})
    check("a description ending in an ellipsis is rejected", False)
except ValidationError as exc:
    check("a description ending in an ellipsis is rejected", "truncated" in exc.reason)

print("normalize_opportunity end to end")
normalized = normalize_opportunity(
    {"title": "  Data   Analyst Internship  ", "description": "Some real description text here for the role."},
    company_slug="kcb-bank-kenya",
    source_url="https://example.com/kcb/data-analyst",
)
check("title is cleaned", normalized["title"] == "Data Analyst Internship")
check("type is inferred", normalized["type"] == "internship")
check("company_slug passes through", normalized["company_slug"] == "kcb-bank-kenya")

print("safaricom.parse_list against synthetic HTML matching the real confirmed URL pattern")
synthetic_html = """
<html><body>
  <div class="featured-role">
    <a href="https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/1401">Project Manager - Fixed Term Contract</a>
  </div>
  <div class="another-role">
    <a href="https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/1402">Software Engineering Intern</a>
  </div>
  <a href="/about">About Us</a>
</body></html>
"""
results = safaricom.parse_list(synthetic_html)
check("finds exactly the two job links, not the unrelated /about link", len(results) == 2)
check("first result has the right title", results[0]["title"] == "Project Manager - Fixed Term Contract")
check("first result has the right detail_url", results[0]["detail_url"].endswith("/job/1401"))
check("second result has the right title", results[1]["title"] == "Software Engineering Intern")

print("safaricom.parse_list against the REAL pattern: empty <a>, title via aria-labelledby")
real_pattern_html = """
<html><body>
  <div class="job-grid-item">
    <a data-bind="click: () =&gt; openJobPreview(job.id)" href="https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/1438" aria-labelledby="1438"></a>
    <div class="job-grid-item__link" data-bind="click: () =&gt; openJobPreview(job.id)">
        <div id="1438" class="job-title">Engineer - Managed Security SolutionsLocationsKenyaPosting Date11/08/2026</div>
    </div>
  </div>
</body></html>
"""
real_results = safaricom.parse_list(real_pattern_html)
check("finds the job despite the empty <a> tag", len(real_results) == 1)
check("title is cleanly split, not the raw concatenated blob", real_results[0]["title"] == "Engineer - Managed Security Solutions")
check("county is recovered from the same blob", real_results[0]["county"] == "Kenya")
check("still gets the right detail_url", real_results[0]["detail_url"].endswith("/job/1438"))

print("_split_card_text against the actual titles from Elvis's real run")
r1 = _split_card_text("Engineer - Managed Security SolutionsLocationsKenyaPosting Date11/08/2026")
check("real title 1: clean title", r1["title"] == "Engineer - Managed Security Solutions")
check("real title 1: county", r1["location"] == "Kenya")
check("real title 1: not hybrid", r1["is_hybrid"] is False)

r2 = _split_card_text("Research Manager\u2013 FuturistLocationsKenya(Hybrid)Posting Date10/08/2026Trending")
check("real title 2: clean title keeps the company's own dash in the title itself", r2["title"] == "Research Manager\u2013 Futurist")
check("real title 2: county strips the (Hybrid) qualifier", r2["location"] == "Kenya")
check("real title 2: is_hybrid detected", r2["is_hybrid"] is True)

r4 = _split_card_text("Segment marketing Manager \u2013 Mass MarketLocationsKenyaPosting Date10/08/2026Trending")
check("real title 4: clean title", r4["title"] == "Segment marketing Manager \u2013 Mass Market")
check("real title 4: county", r4["location"] == "Kenya")

print("_split_card_text falls back gracefully on an unrecognized shape")
fallback = _split_card_text("Just A Plain Title With No Metadata")
check("fallback keeps the whole string as the title", fallback["title"] == "Just A Plain Title With No Metadata")
check("fallback location is None", fallback["location"] is None)

print("safaricom.parse_detail against the confirmed real detail-page markup shape")
detail_html = """
<html><body>
  <div data-bind="html: pageData().job.description" class="job-details__description-content">
    <p>Reporting to the Manager, Enterprise IoT and Managed Security Deployment.</p>
    <p>This role drives the technical, operational, commercial, and regulatory success.</p>
  </div>
  <ul>
    <li class="job-meta__item">
      <span class="job-meta__title">Job Identification</span>
      <span class="job-meta__subitem">1410</span>
    </li>
    <li class="job-meta__item">
      <span class="job-meta__title">Apply Before</span>
      <span class="job-meta__subitem">17/08/2026, 00:00</span>
    </li>
  </ul>
</body></html>
"""
detail = safaricom.parse_detail(detail_html)
check(
    "description is extracted with real content from both paragraphs",
    "Reporting to the Manager" in detail["description"] and "regulatory success" in detail["description"],
)
check("requirements is honestly None, not guessed at", detail["requirements"] is None)
check("responsibilities is honestly None, not guessed at", detail["responsibilities"] is None)
check("deadline is found via the sibling span, not the Job Identification one", detail["application_deadline"] == date(2026, 8, 17))

print("safaricom._find_meta_value ignores a same-labeled span with no matching sibling class")
from selectolax.parser import HTMLParser as _HP
tree_only_html = '<span class="job-meta__title">Apply Before</span><span class="something-else">not it</span>'
no_sibling_result = safaricom._find_meta_value(_HP(tree_only_html), "Apply Before")
check("returns None rather than the wrong sibling when the class doesn't match", no_sibling_result is None)

print("safaricom.parse_detail when the description div is missing entirely")
empty_detail = safaricom.parse_detail("<html><body><p>nothing relevant here</p></body></html>")
check("description is None rather than raising", empty_detail["description"] is None)
check("deadline is None rather than raising", empty_detail["application_deadline"] is None)

print(f"\n{passed} passed, {failed} failed")
if failed:
    sys.exit(1)
