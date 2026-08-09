"""Database access for companies — listing and single lookup by slug."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(
        self, *, industry: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Company], int]:
        filters = []
        if industry:
            filters.append(Company.industry.ilike(industry))

        count_base = select(Company.id).where(*filters)
        total = (await self.db.execute(select(func.count()).select_from(count_base.subquery()))).scalar_one()

        stmt = (
            select(Company)
            .where(*filters)
            .order_by(Company.name.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self.db.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()
