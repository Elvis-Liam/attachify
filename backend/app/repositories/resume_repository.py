"""Database access for resumes."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, user_id: uuid.UUID, template: str, content: dict) -> Resume:
        resume = Resume(user_id=user_id, template=template, content=content)
        self.db.add(resume)
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def get_by_id(self, resume_id: uuid.UUID) -> Resume | None:
        return await self.db.get(Resume, resume_id)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Resume]:
        result = await self.db.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, resume: Resume, *, template: str | None, content: dict | None) -> Resume:
        if template is not None:
            resume.template = template
        if content is not None:
            resume.content = content
        await self.db.commit()
        await self.db.refresh(resume)
        return resume

    async def delete(self, resume: Resume) -> None:
        await self.db.delete(resume)
        await self.db.commit()
