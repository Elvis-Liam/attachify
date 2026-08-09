"""Database access for bookmarked (saved) opportunities."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.opportunity import Opportunity
from app.models.saved_opportunity import SavedOpportunity


class SavedOpportunityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: uuid.UUID, opportunity_id: uuid.UUID) -> SavedOpportunity | None:
        result = await self.db.execute(
            select(SavedOpportunity).where(
                SavedOpportunity.user_id == user_id, SavedOpportunity.opportunity_id == opportunity_id
            )
        )
        return result.scalar_one_or_none()

    async def save(self, user_id: uuid.UUID, opportunity_id: uuid.UUID) -> tuple[SavedOpportunity, bool]:
        """Idempotent — returns (record, created). created is False if it was already saved."""
        existing = await self.get(user_id, opportunity_id)
        if existing is not None:
            return existing, False
        record = SavedOpportunity(user_id=user_id, opportunity_id=opportunity_id)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record, True

    async def unsave(self, user_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        """Idempotent — a no-op if it wasn't saved to begin with."""
        existing = await self.get(user_id, opportunity_id)
        if existing is not None:
            await self.db.delete(existing)
            await self.db.commit()

    async def list_for_user(
        self, user_id: uuid.UUID, *, page: int = 1, per_page: int = 20
    ) -> tuple[list[Opportunity], int]:
        count_base = (
            select(Opportunity.id)
            .join(SavedOpportunity, SavedOpportunity.opportunity_id == Opportunity.id)
            .where(SavedOpportunity.user_id == user_id)
        )
        total = (await self.db.execute(select(func.count()).select_from(count_base.subquery()))).scalar_one()

        stmt = (
            select(Opportunity)
            .join(SavedOpportunity, SavedOpportunity.opportunity_id == Opportunity.id)
            .join(Company, Opportunity.company_id == Company.id)
            .where(SavedOpportunity.user_id == user_id)
            .options(selectinload(Opportunity.company))
            .order_by(SavedOpportunity.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
