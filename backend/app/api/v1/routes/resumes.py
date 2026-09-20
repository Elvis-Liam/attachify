"""Resume CRUD and export endpoints. Every route requires auth, and ownership is
checked on every single-resume operation: a resume belonging to someone else
returns the same 404 as one that doesn't exist, so a guessed ID can't be used to
probe which resumes exist.
"""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeCreate, ResumeOut, ResumeSummary, ResumeUpdate
from app.services.resume_pdf import generate_resume_pdf

router = APIRouter(prefix="/resumes", tags=["resumes"])


async def _get_owned_resume(
    resume_id: uuid.UUID, current_user: User, db: AsyncSession
) -> tuple[Resume, ResumeRepository]:
    repo = ResumeRepository(db)
    resume = await repo.get_by_id(resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found.")
    return resume, repo


def _download_filename(resume: Resume, extension: str) -> str:
    """Build a safe download filename from the person's own name.

    Strips anything that isn't alphanumeric, space, dash, or underscore: a name
    field is free text, and unsanitized user input in a Content-Disposition
    header is a header-injection risk, not just a cosmetic issue.
    """
    personal = (resume.content or {}).get("personal") or {}
    raw_name = str(personal.get("full_name") or "resume")
    safe = re.sub(r"[^A-Za-z0-9 _-]", "", raw_name).strip() or "resume"
    return f"{safe.replace(' ', '_')}_Resume.{extension}"


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED)
async def create_resume(
    data: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Resume:
    return await ResumeRepository(db).create(
        user_id=current_user.id,
        template=data.template,
        content=data.content.model_dump(mode="json"),
    )


@router.get("", response_model=list[ResumeSummary])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Resume]:
    return await ResumeRepository(db).list_for_user(current_user.id)


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Resume:
    resume, _ = await _get_owned_resume(resume_id, current_user, db)
    return resume


@router.patch("/{resume_id}", response_model=ResumeOut)
async def update_resume(
    resume_id: uuid.UUID,
    data: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Resume:
    resume, repo = await _get_owned_resume(resume_id, current_user, db)
    content_dict = data.content.model_dump(mode="json") if data.content is not None else None
    return await repo.update(resume, template=data.template, content=content_dict)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    resume, repo = await _get_owned_resume(resume_id, current_user, db)
    await repo.delete(resume)


@router.get("/{resume_id}/export")
async def export_resume(
    resume_id: uuid.UUID,
    format: str = Query("pdf", pattern="^(pdf)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and download the resume.

    Built on demand rather than served from stored files: a resume is small and
    fast to render, and this way the download always reflects the latest saved
    content with no stale-file problem and no dependency on object storage being
    configured. The format pattern currently accepts only pdf; DOCX is a planned
    addition and will extend that pattern rather than change this shape.
    """
    resume, _ = await _get_owned_resume(resume_id, current_user, db)
    pdf_bytes = generate_resume_pdf(resume.content or {}, resume.template)
    filename = _download_filename(resume, "pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
