"""Validate a normalized record before it's allowed anywhere near the database.

This is the one place that decides "complete enough to store" versus "discard
and log why", so that decision lives in one auditable spot rather than being
scattered across every source's parser.
"""


class ValidationError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


REQUIRED_FIELDS = ("title", "description", "company_slug", "source_url")


def validate_opportunity(record: dict) -> None:
    """Raise ValidationError with a specific reason if the record isn't
    complete enough to store. Returns None (does not mutate) if it's fine.
    """
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            raise ValidationError(f"missing required field: {field}")

    if len(record["title"]) > 255:
        raise ValidationError("title exceeds 255 characters")

    if len(record["description"]) < 20:
        # Deliberately strict: a two-word "description" is exactly the kind
        # of shortened, low-value listing SRS section 10 rules out. Better to
        # skip a record than store something that isn't a real posting yet.
        raise ValidationError("description too short to be a real posting (min 20 characters)")

    if record["description"].rstrip().endswith(("...", "…")):
        # A list-page teaser cut off mid-sentence, exactly what parse_detail
        # exists to replace with the real, full text. Confirmed this pattern
        # is real, not hypothetical: Safaricom's own search results end this
        # way ("...we are looking f...").
        raise ValidationError("description looks truncated (ends with an ellipsis); needs the full detail page")
