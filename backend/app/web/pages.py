"""Server-rendered public pages — home, search, opportunity detail.

Separate from app/api/v1, which serves JSON. These return HTML, and are excluded
from the OpenAPI schema since they aren't part of the API surface.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.enums import OpportunityType
from app.repositories.company_repository import CompanyRepository
from app.repositories.opportunity_repository import OpportunityRepository

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
    # HTMX marks its own requests with this header — return just the results partial
    # for those, and the full page (with the same partial included) for a normal visit.
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request=request, name="partials/_results.html", context=context)
    return templates.TemplateResponse(request=request, name="search.html", context=context)


@router.get("/opportunities/{opportunity_id}")
async def opportunity_detail(request: Request, opportunity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    opportunity = await OpportunityRepository(db).get_by_id(opportunity_id)
    if opportunity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Opportunity not found.")
    return templates.TemplateResponse(
        request=request, name="opportunity_detail.html", context={"opportunity": opportunity}
    )
