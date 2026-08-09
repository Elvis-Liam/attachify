"""Database access for opportunities — search/filter/paginate and single lookups."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.enums import OpportunityStatus, OpportunityType
from app.models.opportunity import Opportunity


class OpportunityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        *,
        keyword: str | None = None,
        county: str | None = None,
        industry: str | None = None,
        company_id: uuid.UUID | None = None,
        type: OpportunityType | None = None,
        is_paid: bool | None = None,
        is_remote: bool | None = None,
        is_hybrid: bool | None = None,
        sort: str = "newest",
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Opportunity], int]:
        filters = [Opportunity.status == OpportunityStatus.ACTIVE]
        if keyword:
            filters.append(Opportunity.search_vector.op("@@")(func.plainto_tsquery("english", keyword)))
        if county:
            filters.append(Opportunity.county.ilike(county))
        if industry:
            filters.append(Company.industry.ilike(industry))
        if company_id:
            filters.append(Opportunity.company_id == company_id)
        if type:
            filters.append(Opportunity.type == type)
        if is_paid is not None:
            filters.append(Opportunity.is_paid == is_paid)
        if is_remote is not None:
            filters.append(Opportunity.is_remote == is_remote)
        if is_hybrid is not None:
            filters.append(Opportunity.is_hybrid == is_hybrid)

        count_base = select(Opportunity.id).join(Company, Opportunity.company_id == Company.id).where(*filters)
        total = (await self.db.execute(select(func.count()).select_from(count_base.subquery()))).scalar_one()

        stmt = (
            select(Opportunity)
            .join(Company, Opportunity.company_id == Company.id)
            .where(*filters)
            .options(selectinload(Opportunity.company))
        )
        stmt = (
            stmt.order_by(Opportunity.application_deadline.asc().nulls_last())
            if sort == "deadline"
            else stmt.order_by(Opportunity.created_at.desc())
        )
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, opportunity_id: uuid.UUID) -> Opportunity | None:
        result = await self.db.execute(
            select(Opportunity)
            .where(Opportunity.id == opportunity_id)
            .options(selectinload(Opportunity.company))
        )
        return result.scalar_one_or_none()
