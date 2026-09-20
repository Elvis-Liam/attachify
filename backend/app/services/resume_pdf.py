"""Resume PDF generation with ReportLab.

Generated on demand and returned as bytes rather than written to disk or object
storage: a resume is small, fast to build, and always reflects the latest saved
content this way, with no stale-file invalidation problem and no dependency on
R2 being configured yet. If generation ever becomes a bottleneck, caching the
bytes is a change local to this module.

The four templates are genuinely different documents, not one layout with
different colors:
  modern:       accent-colored headings, sans-serif, section rules
  professional: conservative serif, centered header block
  ats_friendly: no color, no rules, plain headings, single column, the shape
                applicant tracking systems parse most reliably
  student:      education before experience, since that's what a student leads
                with when they have little work history
"""
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#0E4EB2")
NAVY_DARK = colors.HexColor("#020C47")
MUTED = colors.HexColor("#5B6B8C")

# Confirmed by rendering actual PDFs and visually checking the output: these
# four render correctly in ReportLab's base Helvetica font. Several more
# obvious choices (a house glyph for location, emoji pins and globes, a few
# geometric shapes) were tried first and rendered as broken boxes instead,
# since Helvetica's built-in glyph set is much smaller than it looks like it
# should be. Don't add another symbol here without checking it the same way.
ICON_PHONE = "\u260E"
ICON_EMAIL = "\u2709"
ICON_LINK = "\u25C6"
ICON_LOCATION = "\u25CF"

TEMPLATES = ("modern", "professional", "ats_friendly", "student")


def _clean(value: Any) -> str:
    """Escape user content before it reaches a Paragraph.

    ReportLab parses Paragraph text as XML-ish markup, so an unescaped "&" or
    "<" in someone's resume (a company name like "Ernst & Young", for instance)
    raises a parse error and breaks the whole document. Not hypothetical: "&"
    is common in real employer names.
    """
    if value is None:
        return ""
    return escape(str(value).strip())


def _styles(template: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    serif = template == "professional"
    body_font = "Times-Roman" if serif else "Helvetica"
    bold_font = "Times-Bold" if serif else "Helvetica-Bold"
    plain = template == "ats_friendly"

    return {
        "name": ParagraphStyle(
            "NameStyle",
            parent=base["Title"],
            fontName=bold_font,
            fontSize=20,
            leading=24,
            spaceAfter=2,
            alignment=TA_CENTER if serif else 0,
            textColor=colors.black,
        ),
        "contact": ParagraphStyle(
            "ContactStyle",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=9.5,
            leading=13,
            textColor=colors.black if plain else colors.HexColor("#444444"),
            alignment=TA_CENTER if serif else 0,
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "SectionStyle",
            parent=base["Heading2"],
            fontName=bold_font,
            fontSize=11.5,
            leading=14,
            spaceBefore=12,
            spaceAfter=4,
            textColor=colors.black if plain else ACCENT,
        ),
        "entry_title": ParagraphStyle(
            "EntryTitle",
            parent=base["Normal"],
            fontName=bold_font,
            fontSize=10.5,
            leading=13,
            spaceAfter=1,
        ),
        "entry_meta": ParagraphStyle(
            "EntryMeta",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=9.5,
            leading=12,
            textColor=colors.black if plain else colors.HexColor("#555555"),
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "BodyStyle",
            parent=base["Normal"],
            fontName=body_font,
            fontSize=10,
            leading=13.5,
            spaceAfter=6,
        ),
    }


def _date_range(start: Any, end: Any, is_current: bool = False) -> str:
    start_text = _clean(start)
    end_text = "Present" if is_current else _clean(end)
    if start_text and end_text:
        return f"{start_text} to {end_text}"
    return start_text or end_text


def _section(story: list, title: str, styles: dict, template: str) -> None:
    story.append(Paragraph(title.upper(), styles["section"]))
    if template != "ats_friendly":
        story.append(HRFlowable(width="100%", thickness=0.6, color=ACCENT, spaceAfter=6))


def _add_education(story: list, entries: list[dict], styles: dict, template: str) -> None:
    if not entries:
        return
    _section(story, "Education", styles, template)
    for entry in entries:
        qualification = _clean(entry.get("qualification"))
        field = _clean(entry.get("field_of_study"))
        heading = f"{qualification} in {field}" if qualification and field else qualification or field
        if heading:
            story.append(Paragraph(heading, styles["entry_title"]))
        meta_parts = [_clean(entry.get("institution")), _date_range(entry.get("start_date"), entry.get("end_date"))]
        grade = _clean(entry.get("grade"))
        if grade:
            meta_parts.append(f"Grade: {grade}")
        meta = " | ".join(p for p in meta_parts if p)
        if meta:
            story.append(Paragraph(meta, styles["entry_meta"]))


def _add_experience(story: list, entries: list[dict], styles: dict, template: str) -> None:
    if not entries:
        return
    _section(story, "Experience", styles, template)
    for entry in entries:
        role = _clean(entry.get("role"))
        if role:
            story.append(Paragraph(role, styles["entry_title"]))
        meta_parts = [
            _clean(entry.get("organization")),
            _date_range(entry.get("start_date"), entry.get("end_date"), entry.get("is_current", False)),
        ]
        meta = " | ".join(p for p in meta_parts if p)
        if meta:
            story.append(Paragraph(meta, styles["entry_meta"]))
        description = _clean(entry.get("description"))
        if description:
            story.append(Paragraph(description, styles["body"]))


def _add_projects(story: list, entries: list[dict], styles: dict, template: str) -> None:
    if not entries:
        return
    _section(story, "Projects", styles, template)
    for entry in entries:
        name = _clean(entry.get("name"))
        if name:
            story.append(Paragraph(name, styles["entry_title"]))
        technologies = entry.get("technologies") or []
        if technologies:
            story.append(Paragraph(", ".join(_clean(t) for t in technologies), styles["entry_meta"]))
        description = _clean(entry.get("description"))
        if description:
            story.append(Paragraph(description, styles["body"]))


def _add_bullet_list(story: list, title: str, items: list[str], styles: dict, template: str) -> None:
    cleaned = [_clean(item) for item in items if _clean(item)]
    if not cleaned:
        return
    _section(story, title, styles, template)
    # bulletFontSize is set explicitly: ReportLab's default "circle" bullet
    # renders at body size, which reads as an oversized filled dot next to
    # 10pt text. Confirmed visually, not assumed.
    story.append(
        ListFlowable(
            [ListItem(Paragraph(item, styles["body"]), leftIndent=14) for item in cleaned],
            bulletType="bullet",
            start="\u2022",
            bulletFontSize=9,
            bulletOffsetY=-1.5,
            leftIndent=14,
        )
    )


def _add_inline_list(story: list, title: str, items: list[str], styles: dict, template: str) -> None:
    """Comma-joined rather than bulleted. Used for skills and languages, where a
    long bullet list wastes a page for what reads fine as one line."""
    cleaned = [_clean(item) for item in items if _clean(item)]
    if not cleaned:
        return
    _section(story, title, styles, template)
    story.append(Paragraph(", ".join(cleaned), styles["body"]))


def _add_certifications(story: list, entries: list[dict], styles: dict, template: str) -> None:
    if not entries:
        return
    _section(story, "Certifications", styles, template)
    for entry in entries:
        parts = [_clean(entry.get("name")), _clean(entry.get("issuer")), _clean(entry.get("date"))]
        line = " | ".join(p for p in parts if p)
        if line:
            story.append(Paragraph(line, styles["body"]))


def _add_references(story: list, entries: list[dict], styles: dict, template: str) -> None:
    if not entries:
        return
    _section(story, "References", styles, template)
    for entry in entries:
        name = _clean(entry.get("name"))
        if name:
            story.append(Paragraph(name, styles["entry_title"]))
        parts = [_clean(entry.get("relationship")), _clean(entry.get("contact"))]
        line = " | ".join(p for p in parts if p)
        if line:
            story.append(Paragraph(line, styles["entry_meta"]))


def _modern_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "ModernName", parent=base["Title"], fontName="Helvetica-Bold", fontSize=22,
            leading=25, textColor=NAVY_DARK, alignment=0, spaceAfter=2,
        ),
        "tagline": ParagraphStyle(
            "ModernTagline", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10,
            leading=13, textColor=ACCENT, spaceAfter=0,
        ),
        "contact": ParagraphStyle(
            "ModernContact", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            leading=14, textColor=NAVY_DARK, alignment=2,
        ),
        "section": ParagraphStyle(
            "ModernSection", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11,
            leading=14, textColor=ACCENT, spaceBefore=0, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ModernBody", parent=base["Normal"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=NAVY_DARK,
        ),
        "date": ParagraphStyle(
            "ModernDate", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            leading=13, textColor=MUTED,
        ),
        "entry_title": ParagraphStyle(
            "ModernEntryTitle", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10,
            leading=13, textColor=NAVY_DARK, spaceAfter=1,
        ),
        "entry_meta": ParagraphStyle(
            "ModernEntryMeta", parent=base["Normal"], fontName="Helvetica", fontSize=9,
            leading=12, textColor=MUTED, spaceAfter=3,
        ),
        "entry_title_sm": ParagraphStyle(
            "ModernEntryTitleSm", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9,
            leading=12, textColor=NAVY_DARK,
        ),
        "entry_meta_sm": ParagraphStyle(
            "ModernEntryMetaSm", parent=base["Normal"], fontName="Helvetica", fontSize=8.5,
            leading=11, textColor=MUTED,
        ),
    }


_ZERO_PADDING = [
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]


def _modern_rule() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#B9C6E6"), spaceBefore=10, spaceAfter=14)


def _modern_header(content: dict, styles: dict, doc_width: float) -> Table:
    personal = content.get("personal") or {}
    left: list = [Paragraph(_clean(personal.get("full_name")) or "Your Name", styles["name"])]

    # No dedicated tagline field in ResumeContent (adding one would mean
    # changing the form too), so this falls back to the most recent
    # experience entry's role, a reasonable default rather than leaving the
    # space empty.
    experience = content.get("experience") or []
    tagline = _clean(experience[0].get("role")) if experience else ""
    if tagline:
        left.append(Paragraph(tagline.upper(), styles["tagline"]))

    right: list = []
    if personal.get("phone"):
        right.append(Paragraph(f"{ICON_PHONE}&nbsp;&nbsp;{_clean(personal['phone'])}", styles["contact"]))
    if personal.get("email"):
        right.append(Paragraph(f"{ICON_EMAIL}&nbsp;&nbsp;{_clean(personal['email'])}", styles["contact"]))
    website = personal.get("portfolio_url") or personal.get("linkedin_url")
    if website:
        right.append(Paragraph(f"{ICON_LINK}&nbsp;&nbsp;{_clean(website)}", styles["contact"]))
    if personal.get("location"):
        right.append(Paragraph(f"{ICON_LOCATION}&nbsp;&nbsp;{_clean(personal['location'])}", styles["contact"]))

    table = Table([[left, right]], colWidths=[doc_width * 0.58, doc_width * 0.42])
    table.setStyle(TableStyle(_ZERO_PADDING + [("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return table


def _modern_dated_entries(entries: list[dict], styles: dict, doc_width: float, *, date_key_fn, title_fn, meta_fn, body_fn=None) -> Table | None:
    """Shared builder for the "date on the left, details on the right" row
    pattern used by Experience, Education, and Achievements alike in the
    reference layout. The four callback functions extract what varies per
    section from one entry dict.
    """
    if not entries:
        return None
    rows = []
    for entry in entries:
        date_cell = [Paragraph(date_key_fn(entry), styles["date"])]
        content_cell = [Paragraph(title_fn(entry), styles["entry_title"])]
        meta = meta_fn(entry)
        if meta:
            content_cell.append(Paragraph(meta, styles["entry_meta"]))
        if body_fn:
            body = body_fn(entry)
            if body:
                content_cell.append(Paragraph(body, styles["body"]))
        rows.append([date_cell, content_cell])
    table = Table(rows, colWidths=[doc_width * 0.19, doc_width * 0.81])
    table.setStyle(TableStyle(_ZERO_PADDING + [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    return table


def _modern_two_column_section(left_title: str, left_flowables: list, right_title: str, right_flowables: list, styles: dict, doc_width: float) -> Table | None:
    if not left_flowables and not right_flowables:
        return None
    left = [Paragraph(left_title, styles["section"])] + (left_flowables or [Paragraph("", styles["body"])])
    right = [Paragraph(right_title, styles["section"])] + (right_flowables or [Paragraph("", styles["body"])])
    table = Table([[left, right]], colWidths=[doc_width * 0.5, doc_width * 0.5])
    table.setStyle(TableStyle(_ZERO_PADDING + [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("RIGHTPADDING", (0, 0), (0, 0), 14),
    ]))
    return table


def _build_modern_story(content: dict, doc_width: float) -> list:
    """Two-column layout modeled directly on a reference design Elvis
    provided (a common "designer resume" template shape: name and contact
    header, About Me, Experience with dates in a left rail, then Education
    and Expertise side by side, then Achievements and References side by
    side), recolored into the site's navy/blue palette rather than the
    original grayscale. This is a genuinely different construction from the
    other three templates: it uses ReportLab Tables for the side-by-side
    sections, which a single flowing column can't produce.
    """
    styles = _modern_styles()
    personal = content.get("personal") or {}
    story: list = [_modern_header(content, styles, doc_width)]

    summary = _clean(personal.get("summary"))
    if summary:
        story.append(_modern_rule())
        story.append(Paragraph("ABOUT ME", styles["section"]))
        story.append(Paragraph(summary, styles["body"]))

    experience = content.get("experience") or []
    if experience:
        story.append(_modern_rule())
        story.append(Paragraph("EXPERIENCE", styles["section"]))
        story.append(_modern_dated_entries(
            experience, styles, doc_width,
            date_key_fn=lambda e: _date_range(e.get("start_date"), e.get("end_date"), e.get("is_current", False)),
            title_fn=lambda e: _clean(e.get("role")),
            meta_fn=lambda e: _clean(e.get("organization")),
            body_fn=lambda e: _clean(e.get("description")),
        ))

    education = content.get("education") or []
    skills = content.get("skills") or []
    if education or skills:
        story.append(_modern_rule())
        edu_flowables = []
        for edu in education:
            qualification = _clean(edu.get("qualification"))
            field = _clean(edu.get("field_of_study"))
            heading = f"{qualification} in {field}" if qualification and field else qualification or field
            edu_flowables.append(Paragraph(_date_range(edu.get("start_date"), edu.get("end_date")), styles["entry_meta_sm"]))
            if heading:
                edu_flowables.append(Paragraph(heading, styles["entry_title_sm"]))
            if edu.get("institution"):
                edu_flowables.append(Paragraph(_clean(edu["institution"]), styles["entry_meta_sm"]))
            edu_flowables.append(Spacer(1, 8))
        skill_flowables = [Paragraph(f"\u2022 {_clean(s)}", styles["body"]) for s in skills]
        story.append(_modern_two_column_section("EDUCATION", edu_flowables, "EXPERTISE", skill_flowables, styles, doc_width))

    achievements = content.get("achievements") or []
    references = content.get("references") or []
    if achievements or references:
        story.append(_modern_rule())
        ach_flowables = []
        for item in achievements:
            ach_flowables.append(Paragraph(_clean(item), styles["entry_title_sm"]))
            ach_flowables.append(Spacer(1, 6))
        ref_flowables = []
        for ref in references:
            ref_flowables.append(Paragraph(_clean(ref.get("name")), styles["entry_title_sm"]))
            parts = [p for p in [_clean(ref.get("relationship")), _clean(ref.get("contact"))] if p]
            if parts:
                ref_flowables.append(Paragraph(" | ".join(parts), styles["entry_meta_sm"]))
            ref_flowables.append(Spacer(1, 8))
        story.append(_modern_two_column_section("ACHIEVEMENT", ach_flowables, "REFERENCE", ref_flowables, styles, doc_width))

    projects = content.get("projects") or []
    languages = content.get("languages") or []
    certifications = content.get("certifications") or []
    if projects or languages or certifications:
        story.append(_modern_rule())
        if projects:
            story.append(Paragraph("PROJECTS", styles["section"]))
            for p in projects:
                name = _clean(p.get("name"))
                if name:
                    story.append(Paragraph(name, styles["entry_title"]))
                techs = p.get("technologies") or []
                if techs:
                    story.append(Paragraph(", ".join(_clean(t) for t in techs), styles["entry_meta"]))
                description = _clean(p.get("description"))
                if description:
                    story.append(Paragraph(description, styles["body"]))
                story.append(Spacer(1, 6))
        extras = []
        if languages:
            extras.append(", ".join(_clean(x) for x in languages))
        if certifications:
            for c in certifications:
                parts = [p for p in [_clean(c.get("name")), _clean(c.get("issuer")), _clean(c.get("date"))] if p]
                if parts:
                    extras.append(" | ".join(parts))
        if extras:
            story.append(Paragraph("Languages & Certifications", styles["entry_title_sm"]))
            for line in extras:
                story.append(Paragraph(line, styles["body"]))

    if len(story) <= 1:
        story.append(Spacer(1, 14))
        story.append(Paragraph("This resume doesn't have any content yet.", styles["body"]))
    return story


def generate_resume_pdf(content: dict, template: str = "modern") -> bytes:
    """Render resume content to PDF bytes.

    content matches the ResumeContent schema (app/schemas/resume.py). Missing or
    empty sections are simply skipped, so a half-filled resume still produces a
    clean document rather than a page of empty headings.
    """
    if template not in TEMPLATES:
        template = "modern"

    buffer = BytesIO()
    left_margin, right_margin, top_margin, bottom_margin = 18 * mm, 18 * mm, 16 * mm, 16 * mm
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title=_clean((content.get("personal") or {}).get("full_name")) or "Resume",
    )

    if template == "modern":
        doc_width = A4[0] - left_margin - right_margin
        story = _build_modern_story(content, doc_width)
        doc.build(story)
        return buffer.getvalue()

    styles = _styles(template)
    personal = content.get("personal") or {}
    story = []

    full_name = _clean(personal.get("full_name"))
    if full_name:
        story.append(Paragraph(full_name, styles["name"]))

    contact_bits = [
        _clean(personal.get("email")),
        _clean(personal.get("phone")),
        _clean(personal.get("location")),
        _clean(personal.get("linkedin_url")),
        _clean(personal.get("portfolio_url")),
    ]
    contact_line = "  |  ".join(b for b in contact_bits if b)
    if contact_line:
        story.append(Paragraph(contact_line, styles["contact"]))

    summary = _clean(personal.get("summary"))
    if summary:
        _section(story, "Summary", styles, template)
        story.append(Paragraph(summary, styles["body"]))

    education = content.get("education") or []
    experience = content.get("experience") or []

    # The student template leads with education, since that's what a student
    # with little work history actually has to show first.
    if template == "student":
        _add_education(story, education, styles, template)
        _add_experience(story, experience, styles, template)
    else:
        _add_experience(story, experience, styles, template)
        _add_education(story, education, styles, template)

    _add_projects(story, content.get("projects") or [], styles, template)
    _add_inline_list(story, "Skills", content.get("skills") or [], styles, template)
    _add_certifications(story, content.get("certifications") or [], styles, template)
    _add_bullet_list(story, "Achievements", content.get("achievements") or [], styles, template)
    _add_inline_list(story, "Languages", content.get("languages") or [], styles, template)
    _add_references(story, content.get("references") or [], styles, template)

    if not story:
        story.append(Paragraph("This resume is empty.", styles["body"]))

    doc.build(story)
    return buffer.getvalue()
