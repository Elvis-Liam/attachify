"""Company listing and detail endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.company_repository import CompanyRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.schemas.company import CompanyBrief, PaginatedCompanies
from app.schemas.opportunity import CompanyWithOpportunities, OpportunitySummary

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedCompanies)
async def list_companies(
    industry: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedCompanies:
    companies, total = await CompanyRepository(db).list_all(industry=industry, page=page, per_page=per_page)
    return PaginatedCompanies(
        results=[CompanyBrief.model_validate(c) for c in companies],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{slug}", response_model=CompanyWithOpportunities)
async def get_company(slug: str, db: AsyncSession = Depends(get_db)) -> CompanyWithOpportunities:
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found.")

    opportunities, _ = await OpportunityRepository(db).search(company_id=company.id, per_page=50)

    return CompanyWithOpportunities(
        id=company.id,
        name=company.name,
        slug=company.slug,
        industry=company.industry,
        verified=company.verified,
        county=company.county,
        town=company.town,
        website=company.website,
        description=company.description,
        opportunities=[OpportunitySummary.model_validate(o) for o in opportunities],
    )
