"""One-off script that populates a handful of real, varied sample companies and
opportunities so Phase 1's search API has something real to query.

Run with: python -m app.scripts.seed_sample_data

This is NOT the scraper. The scraper (later in Phase 1) replaces this with real,
continuously refreshed listings pulled in full from actual company sites; see the
note in app/web/pages.py and SRS section 10 for the "capture the whole posting,
never a summary" principle that governs how that data gets extracted.

Safe to re-run: companies are skipped if they already exist by slug, and
opportunities are updated in place if the same company and title already exist,
so editing the content below and re-running applies the changes.
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
        "description": (
            "Safaricom's technology team is looking for a software engineering intern to "
            "join a product squad building tools used by millions of customers daily. You "
            "will work alongside senior engineers on real production code, from initial "
            "design through to release, gaining exposure to the full software development "
            "lifecycle at one of East Africa's largest technology employers. This is a "
            "structured, mentored internship; interns are expected to ship real, working "
            "features by the end of the term."
        ),
        "requirements": (
            "Currently pursuing a degree in Computer Science, Software Engineering, "
            "Information Technology, or a closely related field, in your third year or "
            "later. Working knowledge of at least one modern programming language, Python, "
            "Java, or JavaScript preferred. Comfortable with Git and basic command line "
            "tools. No prior professional experience required."
        ),
        "responsibilities": (
            "Write and test code for customer facing features under the guidance of a "
            "senior engineer. Participate in daily stand ups, sprint planning, and code "
            "review as a full member of the squad. Debug and fix issues identified in "
            "staging and production environments. Document your work clearly enough for "
            "the next engineer to pick it up. Present a short demo of your contribution at "
            "the end of the internship."
        ),
        "county": "Nairobi", "town": "Westlands",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 25000, "deadline_days": 30,
    },
    {
        "company_slug": "safaricom",
        "title": "Network Operations Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": (
            "This attachment places you inside Safaricom's Network Operations Centre, the "
            "team responsible for keeping voice, data, and M-PESA services running across "
            "the country around the clock. You will shadow experienced network engineers, "
            "learn how a national telecom network is monitored and maintained, and get "
            "hands on exposure to the tools used to detect and resolve faults before "
            "customers notice them."
        ),
        "requirements": (
            "Diploma or degree in Telecommunications Engineering, Electrical and "
            "Electronic Engineering, or a related technical field. Basic understanding of "
            "networking concepts from coursework is an advantage but not mandatory. "
            "Willingness to work shift patterns, since network operations run "
            "continuously."
        ),
        "responsibilities": (
            "Monitor network performance dashboards and escalate anomalies according to "
            "established procedures. Assist senior engineers with fault diagnosis and root "
            "cause analysis. Maintain accurate logs of incidents and resolutions. Support "
            "routine maintenance activities under supervision. Learn and apply Safaricom's "
            "incident management framework."
        ),
        "county": "Nairobi", "town": "Westlands",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 15000, "deadline_days": 45,
    },
    {
        "company_slug": "kcb-bank-kenya",
        "title": "Finance Graduate Trainee Program",
        "type": OpportunityType.GRADUATE_PROGRAM,
        "description": (
            "KCB's Graduate Trainee Program is an eighteen month rotational program that "
            "moves participants through finance, credit risk, treasury, and retail banking "
            "functions before placement into a permanent role. It is designed for "
            "graduates who want a genuine foundation in banking rather than a narrow first "
            "job, combining structured classroom training with real rotational assignments "
            "across the bank."
        ),
        "requirements": (
            "A first degree, upper second class or above, in Finance, Economics, "
            "Accounting, or a related business field, completed within the last two years. "
            "Progress toward CPA, ACCA, or CFA is an advantage though not required at "
            "entry. Strong analytical and Excel skills. Kenyan citizenship and eligibility "
            "to work in Kenya."
        ),
        "responsibilities": (
            "Complete a structured classroom induction covering banking fundamentals and "
            "KCB's products. Rotate through at least three departments over the program, "
            "taking on real analytical and reporting work in each. Prepare periodic "
            "performance reviews with your program mentor. Complete a capstone project in "
            "your final rotation, presented to senior management."
        ),
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 60000, "deadline_days": 60,
    },
    {
        "company_slug": "kcb-bank-kenya",
        "title": "Data Analyst Internship",
        "type": OpportunityType.INTERNSHIP,
        "description": (
            "Join KCB's retail banking analytics team for a hands on internship "
            "supporting the reporting and dashboards that inform decisions across the "
            "branch network. You will work with real, anonymized transaction data, "
            "learning how a bank actually uses data day to day rather than working "
            "through textbook exercises."
        ),
        "requirements": (
            "Currently pursuing or recently completed a degree in Statistics, Data "
            "Science, Actuarial Science, Economics, or a related quantitative field. "
            "Working knowledge of SQL is required. Familiarity with a BI tool such as "
            "Power BI or Tableau, or with Python or R, is an advantage."
        ),
        "responsibilities": (
            "Build and maintain recurring reports for the retail banking team. Query and "
            "clean data from KCB's internal systems using SQL. Support ad hoc analysis "
            "requests from business stakeholders. Document data definitions and report "
            "logic for handover. Present findings clearly to non technical audiences."
        ),
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 20000, "deadline_days": 20,
    },
    {
        "company_slug": "kenyatta-national-hospital",
        "title": "Nursing Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": (
            "This clinical attachment places nursing students across general wards at "
            "Kenyatta National Hospital, Kenya's largest referral hospital, under the "
            "direct supervision of registered nursing staff. It is intended to fulfil the "
            "practical clinical hours required by nursing training programs, giving "
            "students exposure to a high volume, high acuity public hospital environment."
        ),
        "requirements": (
            "Currently enrolled in a diploma or degree Nursing program at a KMTC "
            "accredited institution or recognized university. Valid student registration "
            "with the Nursing Council of Kenya. Up to date immunization records, including "
            "Hepatitis B. Professional conduct and patient confidentiality are strictly "
            "required."
        ),
        "responsibilities": (
            "Assist registered nurses with routine patient care under direct supervision. "
            "Take and record patient vital signs. Support ward rounds and documentation. "
            "Observe and, where permitted, assist with clinical procedures appropriate to "
            "your training level. Maintain accurate, timely patient records in line with "
            "hospital policy."
        ),
        "county": "Nairobi", "town": "Upper Hill",
        "is_remote": False, "is_hybrid": False, "is_paid": False,
        "stipend_amount": None, "deadline_days": 15,
    },
    {
        "company_slug": "bidco-africa",
        "title": "Industrial Attachment: Mechanical Engineering",
        "type": OpportunityType.ATTACHMENT,
        "description": (
            "Bidco Africa's Thika manufacturing plant is one of the largest edible oil and "
            "personal care production facilities in the region. This attachment places "
            "mechanical engineering students within the plant's maintenance engineering "
            "team, working on the machinery that keeps a high volume production line "
            "running."
        ),
        "requirements": (
            "Diploma or degree in Mechanical Engineering, Production Engineering, or a "
            "closely related field. Basic understanding of industrial machinery and "
            "maintenance principles from coursework. Comfortable working on a factory "
            "floor, including standing for extended periods and following strict safety "
            "protocols."
        ),
        "responsibilities": (
            "Support scheduled and breakdown maintenance activities under supervision of a "
            "maintenance engineer. Assist with inspection and basic troubleshooting of "
            "production line equipment. Maintain maintenance logs and spare parts records. "
            "Follow all plant safety, hygiene, and PPE requirements without exception. "
            "Participate in root cause analysis for recurring equipment failures."
        ),
        "county": "Kiambu", "town": "Thika",
        "is_remote": False, "is_hybrid": False, "is_paid": True,
        "stipend_amount": 12000, "deadline_days": 40,
    },
    {
        "company_slug": "amref-health-africa",
        "title": "Public Health Internship",
        "type": OpportunityType.INTERNSHIP,
        "description": (
            "Amref Health Africa is Africa's largest health focused NGO, and this "
            "internship sits within its Kenya country program supporting community health "
            "initiatives. You will contribute to monitoring and evaluation work across "
            "active projects, helping the organization understand whether its programs are "
            "actually reaching and helping the communities they target."
        ),
        "requirements": (
            "Degree in Public Health, Nursing, Community Health, or a related field, "
            "either completed or in final year. Basic data collection and analysis "
            "skills. Willingness to travel occasionally to project sites outside Nairobi. "
            "Strong written communication skills for report writing."
        ),
        "responsibilities": (
            "Support data collection for ongoing monitoring and evaluation activities. "
            "Assist with compiling and cleaning program data. Contribute to donor and "
            "internal reporting under supervision of the M&E team. Participate in "
            "community engagement activities where relevant to the internship. Summarize "
            "findings into clear, non technical language for program teams."
        ),
        "county": "Nairobi", "town": "Lang'ata",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 18000, "deadline_days": 25,
    },
    {
        "company_slug": "sarova-hotels",
        "title": "Hospitality Management Attachment",
        "type": OpportunityType.ATTACHMENT,
        "description": (
            "This rotational attachment moves students through front office, food and "
            "beverage, and housekeeping departments at a Sarova property, giving a genuine "
            "cross section of hotel operations rather than a single narrow role. It is "
            "designed for students who need to complete practical industry hours as part "
            "of a hospitality management qualification."
        ),
        "requirements": (
            "Currently enrolled in a diploma or degree program in Hotel Management, "
            "Hospitality, or Tourism at a recognized institution. Presentable, customer "
            "facing demeanor. Willingness to work shifts, including weekends and public "
            "holidays, as is standard in hotel operations."
        ),
        "responsibilities": (
            "Rotate through front office, food and beverage service, and housekeeping over "
            "the course of the attachment. Assist guests directly under the supervision of "
            "department staff. Learn and follow Sarova's service standards and operating "
            "procedures. Support routine administrative tasks within each department. "
            "Complete a logbook of duties for your training institution's assessment."
        ),
        "county": "Nairobi", "town": "Nairobi CBD",
        "is_remote": False, "is_hybrid": False, "is_paid": False,
        "stipend_amount": None, "deadline_days": 35,
    },
    {
        "company_slug": "twiga-foods",
        "title": "Software Engineering Apprenticeship",
        "type": OpportunityType.APPRENTICESHIP,
        "description": (
            "Twiga Foods runs one of East Africa's largest agritech platforms, connecting "
            "farmers directly to retailers. This six month, paid apprenticeship is a "
            "genuine hands on route into professional software engineering, aimed at "
            "capable developers who may not have a traditional computer science "
            "background but can demonstrate real coding ability."
        ),
        "requirements": (
            "Demonstrated JavaScript or TypeScript ability, through personal projects, "
            "bootcamp work, open source contributions, or prior study; a formal degree is "
            "not required. Comfortable learning quickly and working directly with "
            "production code under mentorship. Based in or able to relocate to Nairobi for "
            "the hybrid work arrangement."
        ),
        "responsibilities": (
            "Build features for Twiga's logistics and ordering platforms alongside an "
            "assigned mentor. Write tests for the code you ship, not just the code itself. "
            "Take part in code review, both giving and receiving feedback. Progress from "
            "small, well scoped tasks toward larger, more independent pieces of work over "
            "the six months. Complete a final project demonstrating what you have "
            "learned."
        ),
        "county": "Nairobi", "town": "Industrial Area",
        "is_remote": False, "is_hybrid": True, "is_paid": True,
        "stipend_amount": 30000, "deadline_days": 50,
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        slug_to_id: dict[str, object] = {}

        print(f"Checking {len(COMPANIES)} companies...")
        for data in COMPANIES:
            existing = (
                await db.execute(select(Company).where(Company.slug == data["slug"]))
            ).scalar_one_or_none()
            if existing:
                slug_to_id[data["slug"]] = existing.id
                print(f"  {data['name']}: already exists")
                continue
            company = Company(**data)
            db.add(company)
            await db.commit()
            slug_to_id[data["slug"]] = company.id
            print(f"  {data['name']}: created")

        print(f"Checking {len(OPPORTUNITIES)} opportunities...")
        created, updated = 0, 0
        for opp in OPPORTUNITIES:
            company_id = slug_to_id[opp["company_slug"]]
            existing = (
                await db.execute(
                    select(Opportunity).where(
                        Opportunity.company_id == company_id, Opportunity.title == opp["title"]
                    )
                )
            ).scalar_one_or_none()

            fields = dict(
                description=opp["description"],
                requirements=opp["requirements"],
                responsibilities=opp["responsibilities"],
                county=opp["county"],
                town=opp["town"],
                is_remote=opp["is_remote"],
                is_hybrid=opp["is_hybrid"],
                is_paid=opp["is_paid"],
                stipend_amount=opp["stipend_amount"],
                application_deadline=date.today() + timedelta(days=opp["deadline_days"]),
            )

            if existing:
                for key, value in fields.items():
                    setattr(existing, key, value)
                await db.commit()
                updated += 1
                print(f"  {opp['title']}: updated")
                continue

            db.add(
                Opportunity(
                    company_id=company_id,
                    title=opp["title"],
                    type=opp["type"],
                    source_url=(
                        f"https://example.com/{opp['company_slug']}/"
                        f"{opp['title'].lower().replace(' ', '-')}"
                    ),
                    **fields,
                )
            )
            await db.commit()
            created += 1
            print(f"  {opp['title']}: created")

        print(f"Done. {len(COMPANIES)} companies checked, {created} new opportunities, {updated} updated.")


if __name__ == "__main__":
    asyncio.run(seed())
