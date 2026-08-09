"""Bookmark (save/unsave) opportunities for the current user."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.opportunity_repository import OpportunityRepository
from app.repositories.saved_opportunity_repository import SavedOpportunityRepository
from app.schemas.opportunity import OpportunitySummary, PaginatedOpportunities

router = APIRouter(prefix="/saved-opportunities", tags=["saved"])


@router.get("", response_model=PaginatedOpportunities)
async def list_saved_opportunities(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedOpportunities:
    opportunities, total = await SavedOpportunityRepository(db).list_for_user(
        current_user.id, page=page, per_page=per_page
    )
    return PaginatedOpportunities(
        results=[OpportunitySummary.model_validate(o) for o in opportunities],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.post("/{opportunity_id}")
async def save_opportunity(
    opportunity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    opportunity = await OpportunityRepository(db).get_by_id(opportunity_id)
    if opportunity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found.")

    _, created = await SavedOpportunityRepository(db).save(current_user.id, opportunity_id)
    return {"message": "Saved." if created else "Already saved."}


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_opportunity(
    opportunity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await SavedOpportunityRepository(db).unsave(current_user.id, opportunity_id)
