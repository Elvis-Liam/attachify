"""One-off script that populates a handful of real, varied sample companies and
opportunities so Phase 1's search API has something real to query.

Run with: python -m app.scripts.seed_sample_data

This is NOT the scraper — the scraper (later in Phase 1) replaces this with real,
continuously-refreshed listings from actual company sites. Safe to re-run: it skips
any company or opportunity that already exists.
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.company import Company
from app.models.enums import OpportunityType
from app.models.opportunity import Opportunity

COMPANIES = [
    {
        "name": "Safaricom PLC",
        "slug": "safaricom",
        "industry": "Telecommunications",
        "county": "Nairobi",
        "town": "Westlands",
        "website": "https://www.safaricom.co.ke",
        "description": "Kenya's leading telecommunications and mobile money provider.",
        "verified": True,
    },
    {
        "name": "KCB Bank Kenya",
        "slug": "kcb-bank-kenya",
        "industry": "Banking & Finance",
        "county": "Nairobi",
        "town": "Nairobi CBD",
        "website": "https://ke.kcbgroup.com",
        "description": "One of East Africa's largest commercial banks.",
        "verified": True,
    },
    {
        "name": "Kenyatta National Hospital",
        "slug": "kenyatta-national-hospital",
        "industry": "Healthcare",
        "county": "Nairobi",
        "town": "Upper Hill",
        "website": "https://knh.or.ke",
        "description": "Kenya's largest national referral and teaching hospital.",
        "verified": True,
    },
    {
        "name": "Bidco Africa",
        "slug": "bidco-africa",
        "industry": "Manufacturing",
        "county": "Kiambu",
        "town": "Thika",
        "website": "https://www.bidco-africa.com",
        "description": "Regional manufacturer of edible oils, fats, and personal care products.",
        "verified": True,
    },
    {
        "name": "Amref Health Africa",
        "slug": "amref-health-africa",
        "industry": "NGO / Non-profit",
        "county": "Nairobi",
        "town": "Lang'ata",
        "website": "https://amref.org",
        "description": "Africa's largest health-focused NGO.",
        "verified": True,
    },
    {
        "name": "Sarova Hotels",
        "slug": "sarova-hotels",
        "industry": "Hospitality",
        "county": "Nairobi",
        "town": "Nairobi CBD",
        "website": "https://www.sarovahotels.com",
        "description": "Kenyan hospitality group operating hotels and resorts countrywide.",
        "verified": True,
    },
    {
        "name": "Twiga Foods",
        "slug": "twiga-foods",
        "industry": "Agritech",
        "county": "Nairobi",
        "town": "Industrial Area",
        "website": "https://twiga.com",
        "description": "Agritech platform connecting farmers to retailers across Kenya.",
        "verified": True,
    },
]

OPPORTUNITIES = [
    {
        "company_slug": "safaricom",
        "title": "Software Engineering Internship",
        "type": OpportunityType.INTERNSHIP,
        "description": "Work alongside Safaricom's engineering teams building customer-facing products.",
        "requirements": "Currently pursuing a degree in Computer Science, IT, or a related field. Python or Java experience.",
        "county": "Nairobi", "town": "Westlands",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 25000, "deadline_days": 30,
    },
    {
        "company_slug": "safaricom",
        "title": "Network Operations Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": "Support the network operations center monitoring Safaricom's national network.",
        "requirements": "Diploma or degree in Telecommunications or Electrical Engineering.",
        "county": "Nairobi", "town": "Westlands",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 15000, "deadline_days": 45,
    },
    {
        "company_slug": "kcb-bank-kenya",
        "title": "Finance Graduate Trainee Program",
        "type": OpportunityType.GRADUATE_PROGRAM,
        "description": "An 18-month rotational program across KCB's finance and credit risk functions.",
        "requirements": "Bachelor's degree in Finance, Economics, or Accounting. CPA or ACCA progress an advantage.",
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 60000, "deadline_days": 60,
    },
    {
        "company_slug": "kcb-bank-kenya",
        "title": "Data Analyst Internship",
        "type": OpportunityType.INTERNSHIP,
        "description": "Support the analytics team with reporting and dashboarding for retail banking.",
        "requirements": "Degree in Statistics, Data Science, or a related field. SQL required.",
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 20000, "deadline_days": 20,
    },
    {
        "company_slug": "kenyatta-national-hospital",
        "title": "Nursing Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": "Clinical attachment across general wards under the supervision of registered nurses.",
        "requirements": "Enrolled in a diploma or degree Nursing program at a recognized institution.",
        "county": "Nairobi", "town": "Upper Hill",
        "is_remote": False, "is_hybrid": False, "is_paid": False,
        "stipend_amount": None, "deadline_days": 15,
    },
    {
        "company_slug": "bidco-africa",
        "title": "Industrial Attachment — Mechanical Engineering",
        "type": OpportunityType.ATTACHMENT,
        "description": "Hands-on attachment within Bidco's production and maintenance engineering teams.",
        "requirements": "Diploma or degree in Mechanical Engineering.",
        "county": "Kiambu", "town": "Thika",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 12000, "deadline_days": 40,
    },
    {
        "company_slug": "amref-health-africa",
        "title": "Public Health Internship",
        "type": OpportunityType.INTERNSHIP,
        "description": "Support community health program monitoring and evaluation across Amref's Kenya projects.",
        "requirements": "Degree in Public Health, Nursing, or a related field.",
        "county": "Nairobi", "town": "Lang'ata",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 18000, "deadline_days": 25,
    },
    {
        "company_slug": "sarova-hotels",
        "title": "Hospitality Management Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": "Rotational attachment across front office, food & beverage, and housekeeping departments.",
        "requirements": "Diploma in Hotel & Hospitality Management.",
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": False, "is_paid": False,
        "stipend_amount": None, "deadline_days": 35,
    },
    {
        "company_slug": "twiga-foods",
        "title": "Software Engineering Apprenticeship",
        "type": OpportunityType.APPRENTICESHIP,
        "description": "A 6-month, paid, hands-on apprenticeship building Twiga's logistics and ordering platforms.",
        "requirements": "Self-taught or formally trained developers welcome. JavaScript/TypeScript experience.",
        "county": "Nairobi", "town": "Industrial Area",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 30000, "deadline_days": 50,
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        slug_to_id: dict[str, object] = {}

        for data in COMPANIES:
            existing = (
                await db.execute(select(Company).where(Company.slug == data["slug"]))
            ).scalar_one_or_none()
            if existing:
                slug_to_id[data["slug"]] = existing.id
                continue
            company = Company(**data)
            db.add(company)
            await db.flush()
            slug_to_id[data["slug"]] = company.id

        created = 0
        for opp in OPPORTUNITIES:
            company_id = slug_to_id[opp["company_slug"]]
            existing = (
                await db.execute(
                    select(Opportunity).where(
                        Opportunity.company_id == company_id, Opportunity.title == opp["title"]
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            db.add(
                Opportunity(
                    company_id=company_id,
                    title=opp["title"],
                    type=opp["type"],
                    description=opp["description"],
                    requirements=opp["requirements"],
                    county=opp["county"],
                    town=opp["town"],
                    is_remote=opp["is_remote"],
                    is_hybrid=opp["is_hybrid"],
                    is_paid=opp["is_paid"],
                    stipend_amount=opp["stipend_amount"],
                    application_deadline=date.today() + timedelta(days=opp["deadline_days"]),
                    source_url=(
                        f"https://example.com/{opp['company_slug']}/"
                        f"{opp['title'].lower().replace(' ', '-')}"
                    ),
                )
            )
            created += 1

        await db.commit()
        print(f"Seeded {len(COMPANIES)} companies and {created} new opportunities.")


if __name__ == "__main__":
    asyncio.run(seed())
