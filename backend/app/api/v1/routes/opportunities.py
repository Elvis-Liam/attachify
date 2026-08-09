"""Opportunity search and detail endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import OpportunityType
from app.repositories.opportunity_repository import OpportunityRepository
from app.schemas.opportunity import OpportunityDetail, OpportunitySummary, PaginatedOpportunities

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=PaginatedOpportunities)
async def search_opportunities(
    keyword: str | None = None,
    county: str | None = None,
    industry: str | None = None,
    company_id: uuid.UUID | None = None,
    type: OpportunityType | None = None,
    is_paid: bool | None = None,
    is_remote: bool | None = None,
    is_hybrid: bool | None = None,
    sort: str = Query("newest", pattern="^(newest|deadline)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedOpportunities:
    opportunities, total = await OpportunityRepository(db).search(
        keyword=keyword,
        county=county,
        industry=industry,
        company_id=company_id,
        type=type,
        is_paid=is_paid,
        is_remote=is_remote,
        is_hybrid=is_hybrid,
        sort=sort,
        page=page,
        per_page=per_page,
    )
    return PaginatedOpportunities(
        results=[OpportunitySummary.model_validate(o) for o in opportunities],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity(opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> OpportunityDetail:
    opportunity = await OpportunityRepository(db).get_by_id(opportunity_id)
    if opportunity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found.")
    return OpportunityDetail.model_validate(opportunity)
