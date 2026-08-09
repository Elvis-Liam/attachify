"""Opportunities (attachments, internships, graduate programs, apprenticeships) and their course tags."""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OpportunityStatus, OpportunityType, enum_values


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[OpportunityType] = mapped_column(
        SAEnum(OpportunityType, name="opportunity_type", create_type=False, values_callable=enum_values),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    responsibilities: Mapped[str | None] = mapped_column(Text)
    county: Mapped[str | None] = mapped_column(String(100), index=True)
    town: Mapped[str | None] = mapped_column(String(100))
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stipend_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    application_deadline: Mapped[date | None] = mapped_column(Date, index=True)
    external_url: Mapped[str | None] = mapped_column(String(500))
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[OpportunityStatus] = mapped_column(
        SAEnum(OpportunityStatus, name="opportunity_status", create_type=False, values_callable=enum_values),
        default=OpportunityStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OpportunityCourse(Base):
    """Join table linking an opportunity to the courses it's relevant to."""

    __tablename__ = "opportunity_courses"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )
