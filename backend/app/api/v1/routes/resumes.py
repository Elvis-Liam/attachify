"""Resume CRUD endpoints. Every route requires auth, and ownership is checked
on every single-resume operation: a resume belonging to someone else returns
the same 404 as one that doesn't exist, so a guessed ID can't be used to
probe which resumes exist.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeCreate, ResumeOut, ResumeSummary, ResumeUpdate

router = APIRouter(prefix="/resumes", tags=["resumes"])


async def _get_owned_resume(
    resume_id: uuid.UUID, current_user: User, db: AsyncSession
) -> tuple[Resume, ResumeRepository]:
    repo = ResumeRepository(db)
    resume = await repo.get_by_id(resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found.")
    return resume, repo


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
