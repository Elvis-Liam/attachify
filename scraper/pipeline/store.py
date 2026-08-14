"""Upsert a validated, normalized opportunity into Postgres.

Deliberately reuses the backend's own SQLAlchemy models rather than
duplicating table definitions here, so there is exactly one place the schema
is defined. This only works because scraper/run.py adds backend/ to
sys.path before anything in this package gets imported; see its top for why.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.enums import OpportunityType
from app.models.opportunity import Opportunity


async def get_or_create_company(db: AsyncSession, *, slug: str, name: str) -> Company:
    existing = (await db.execute(select(Company).where(Company.slug == slug))).scalar_one_or_none()
    if existing:
        return existing
    company = Company(name=name, slug=slug, industry="Unknown", verified=False)
    db.add(company)
    await db.flush()
    return company


async def upsert_opportunity(db: AsyncSession, *, record: dict, company_name: str) -> tuple[Opportunity, bool]:
    """Insert a new opportunity, or update it in place if source_url already
    exists. Returns (opportunity, created)."""
    existing = (
        await db.execute(select(Opportunity).where(Opportunity.source_url == record["source_url"]))
    ).scalar_one_or_none()

    company = await get_or_create_company(db, slug=record["company_slug"], name=company_name)

    fields = dict(
        title=record["title"],
        type=OpportunityType(record["type"]),
        description=record["description"],
        requirements=record.get("requirements"),
        responsibilities=record.get("responsibilities"),
        county=record.get("county"),
        town=record.get("town"),
        is_remote=record.get("is_remote", False),
        is_hybrid=record.get("is_hybrid", False),
        is_paid=record.get("is_paid", False),
        stipend_amount=record.get("stipend_amount"),
        application_deadline=record.get("application_deadline"),
        external_url=record.get("external_url"),
    )

    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        await db.commit()
        return existing, False

    opportunity = Opportunity(company_id=company.id, source_url=record["source_url"], **fields)
    db.add(opportunity)
    await db.commit()
    return opportunity, True
