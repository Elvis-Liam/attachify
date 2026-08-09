"""Response schemas for company endpoints."""
import uuid

from pydantic import BaseModel, ConfigDict


class CompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    industry: str
    verified: bool


class CompanyDetail(CompanyBrief):
    county: str | None
    town: str | None
    website: str | None
    logo_url: str | None
    description: str | None


class PaginatedCompanies(BaseModel):
    results: list[CompanyBrief]
    page: int
    per_page: int
    total: int
