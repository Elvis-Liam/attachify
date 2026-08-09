"""Response schemas for opportunity endpoints."""
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.schemas.company import CompanyBrief


class OpportunitySummary(BaseModel):
    """Lightweight shape used in search results — enough to render a result card."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: CompanyBrief
    type: str
    county: str | None
    is_remote: bool
    is_paid: bool
    application_deadline: date | None


class OpportunityDetail(OpportunitySummary):
    """Full shape for a single opportunity's detail page."""

    description: str
    requirements: str | None
    responsibilities: str | None
    town: str | None
    is_hybrid: bool
    stipend_amount: float | None
    external_url: str | None
    source_url: str
    status: str


class PaginatedOpportunities(BaseModel):
    results: list[OpportunitySummary]
    page: int
    per_page: int
    total: int


class CompanyWithOpportunities(CompanyBrief):
    """Company detail page shape — profile plus its current active opportunities."""

    county: str | None
    town: str | None
    website: str | None
    description: str | None
    opportunities: list[OpportunitySummary]
