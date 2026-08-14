"""Server-rendered public pages: home, search, opportunity detail, companies,
plus SEO infrastructure (sitemap, robots.txt, structured data).

Separate from app/api/v1, which serves JSON. These return HTML, and are excluded
from the OpenAPI schema since they aren't part of the API surface.
"""
import uuid
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import OpportunityType
from app.repositories.company_repository import CompanyRepository
from app.repositories.opportunity_repository import OpportunityRepository
from app.web.seo import job_posting_json_ld

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    featured, total_opportunities = await OpportunityRepository(db).search(per_page=3, sort="newest")
    _, total_companies = await CompanyRepository(db).list_all(per_page=1)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "featured_opportunities": featured,
            "stats": {"opportunities": total_opportunities, "companies": total_companies},
        },
    )


@router.get("/search")
async def search_page(
    request: Request,
    keyword: str | None = None,
    county: str | None = None,
    type: OpportunityType | None = None,
    is_paid: bool | None = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    opportunities, total = await OpportunityRepository(db).search(
        keyword=keyword, county=county, type=type, is_paid=is_paid, page=page, per_page=12
    )
    context = {
        "opportunities": opportunities,
        "total": total,
        "page": page,
        "filters": {"keyword": keyword, "county": county, "type": type, "is_paid": is_paid},
    }
    # HTMX marks its own requests with this header. Return just the results partial
    # for those, and the full page, which includes the same partial, for a normal visit.
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="partials/_results.html", context=context)
    return templates.TemplateResponse(request=request, name="search.html", context=context)


@router.get("/opportunities/{opportunity_id}")
async def opportunity_detail(request: Request, opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    opportunity = await OpportunityRepository(db).get_by_id(opportunity_id)
    if opportunity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found.")
    return templates.TemplateResponse(
        request=request,
        name="opportunity_detail.html",
        context={
            "opportunity": opportunity,
            "job_posting_ld": job_posting_json_ld(opportunity, str(request.url)),
        },
    )


@router.get("/companies")
async def companies_list(request: Request, db: AsyncSession = Depends(get_db)):
    companies, total = await CompanyRepository(db).list_all(per_page=100)
    return templates.TemplateResponse(
        request=request, name="companies.html", context={"companies": companies, "total": total}
    )


@router.get("/companies/{slug}")
async def company_detail(request: Request, slug: str, db: AsyncSession = Depends(get_db)):
    company = await CompanyRepository(db).get_by_slug(slug)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Company not found.")
    opportunities, _ = await OpportunityRepository(db).search(company_id=company.id, per_page=50)
    return templates.TemplateResponse(
        request=request,
        name="company_detail.html",
        context={"company": company, "opportunities": opportunities},
    )


@router.get("/how-we-verify")
async def verification_methodology(request: Request):
    return templates.TemplateResponse(request=request, name="verification.html", context={})


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(request: Request) -> str:
    sitemap_url = f"{request.base_url}sitemap.xml"
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        f"Sitemap: {sitemap_url}\n"
    )


@router.get("/sitemap.xml")
async def sitemap_xml(request: Request, db: AsyncSession = Depends(get_db)):
    # Fine as a single flat sitemap at today's scale (tens of URLs). Once the real
    # scraper is populating the database at national scale, this should split into
    # a sitemap index once any one sitemap approaches the 50,000 URL limit.
    opportunities, _ = await OpportunityRepository(db).search(per_page=10000)
    companies, _ = await CompanyRepository(db).list_all(per_page=10000)
    base = str(request.base_url).rstrip("/")

    entries = [
        {"loc": f"{base}/", "changefreq": "daily", "priority": "1.0"},
        {"loc": f"{base}/search", "changefreq": "daily", "priority": "0.9"},
        {"loc": f"{base}/companies", "changefreq": "weekly", "priority": "0.6"},
        {"loc": f"{base}/how-we-verify", "changefreq": "monthly", "priority": "0.3"},
    ]
    for opp in opportunities:
        entries.append({
            "loc": f"{base}/opportunities/{opp.id}",
            "lastmod": opp.updated_at.date().isoformat(),
            "changefreq": "daily",
            "priority": "0.8",
        })
    for company in companies:
        entries.append({
            "loc": f"{base}/companies/{company.slug}",
            "lastmod": company.updated_at.date().isoformat(),
            "changefreq": "weekly",
            "priority": "0.5",
        })

    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for entry in entries:
        xml.append("<url>")
        xml.append(f"<loc>{xml_escape(entry['loc'])}</loc>")
        if "lastmod" in entry:
            xml.append(f"<lastmod>{entry['lastmod']}</lastmod>")
        xml.append(f"<changefreq>{entry['changefreq']}</changefreq>")
        xml.append(f"<priority>{entry['priority']}</priority>")
        xml.append("</url>")
    xml.append("</urlset>")

    return Response(content="".join(xml), media_type="application/xml")
