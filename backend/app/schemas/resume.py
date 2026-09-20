"""Schemas for resume content. Stored as JSONB on the Resume model (content
column), so these define the shape of that JSON rather than mapping to
separate tables, one flexible document per resume rather than nine
normalized child tables for something users edit as a whole.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ResumeTemplate = Literal["modern", "professional", "ats_friendly", "student"]

# ~1500 words at a generous 7 characters/word average (word length plus a
# space), rounded up. The frontend enforces the 1500-word limit itself with a
# live counter; this is the server-side backstop for anyone bypassing that,
# not the primary UX.
_LONG_TEXT_MAX_CHARS = 10500


class PersonalDetails(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    summary: str | None = Field(default=None, max_length=_LONG_TEXT_MAX_CHARS)
    linkedin_url: str | None = None
    portfolio_url: str | None = None


class EducationEntry(BaseModel):
    institution: str
    qualification: str
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None


class ExperienceEntry(BaseModel):
    organization: str
    role: str
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = Field(default=None, max_length=_LONG_TEXT_MAX_CHARS)


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = []
    url: str | None = None


class CertificationEntry(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None


class ReferenceEntry(BaseModel):
    name: str
    relationship: str | None = None
    contact: str | None = None


class ResumeContent(BaseModel):
    personal: PersonalDetails
    education: list[EducationEntry] = []
    experience: list[ExperienceEntry] = []
    projects: list[ProjectEntry] = []
    skills: list[str] = []
    languages: list[str] = []
    certifications: list[CertificationEntry] = []
    achievements: list[str] = []
    references: list[ReferenceEntry] = []


class ResumeCreate(BaseModel):
    template: ResumeTemplate = "modern"
    content: ResumeContent


class ResumeUpdate(BaseModel):
    template: ResumeTemplate | None = None
    content: ResumeContent | None = None


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template: str
    content: dict
    pdf_url: str | None
    docx_url: str | None
    created_at: datetime
    updated_at: datetime


class ResumeSummary(BaseModel):
    """Lightweight shape for listing a user's resumes without the full content."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    template: str
    created_at: datetime
    updated_at: datetime
