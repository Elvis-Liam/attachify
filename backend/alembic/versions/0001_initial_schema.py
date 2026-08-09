"""Initial schema — courses, companies, users, opportunities, and the supporting
directory/application tables. AI-specific tables (chat, embeddings) are deferred to
the Phase 2 migration, since pgvector isn't needed until the AI toolkit is built.

Revision ID: 0001
Revises:
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    bind = op.get_bind()
    postgresql.ENUM("student", "moderator", "admin", name="user_role").create(bind, checkfirst=True)
    postgresql.ENUM("certificate", "diploma", "degree", "postgraduate", name="course_level").create(
        bind, checkfirst=True
    )
    postgresql.ENUM(
        "attachment", "internship", "graduate_program", "apprenticeship", name="opportunity_type"
    ).create(bind, checkfirst=True)
    postgresql.ENUM("active", "expired", "filled", "flagged", name="opportunity_status").create(
        bind, checkfirst=True
    )
    postgresql.ENUM(
        "pending_payment", "submitted", "failed", "cancelled", name="application_status"
    ).create(bind, checkfirst=True)
    postgresql.ENUM("application_fee", "donation", name="payment_type").create(bind, checkfirst=True)
    postgresql.ENUM("pending", "completed", "failed", name="payment_status").create(bind, checkfirst=True)

    user_role = postgresql.ENUM("student", "moderator", "admin", name="user_role", create_type=False)
    course_level = postgresql.ENUM(
        "certificate", "diploma", "degree", "postgraduate", name="course_level", create_type=False
    )
    opportunity_type = postgresql.ENUM(
        "attachment", "internship", "graduate_program", "apprenticeship",
        name="opportunity_type", create_type=False,
    )
    opportunity_status = postgresql.ENUM(
        "active", "expired", "filled", "flagged", name="opportunity_status", create_type=False
    )
    application_status = postgresql.ENUM(
        "pending_payment", "submitted", "failed", "cancelled", name="application_status", create_type=False
    )
    payment_type = postgresql.ENUM("application_fee", "donation", name="payment_type", create_type=False)
    payment_status = postgresql.ENUM("pending", "completed", "failed", name="payment_status", create_type=False)

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("level", course_level, nullable=False),
        sa.Column("field_of_study", sa.String(150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("industry", sa.String(120), nullable=False),
        sa.Column("county", sa.String(100)),
        sa.Column("town", sa.String(100)),
        sa.Column("website", sa.String(255)),
        sa.Column("logo_url", sa.String(255)),
        sa.Column("description", sa.Text()),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_companies_industry", "companies", ["industry"])
    op.create_index("idx_companies_county", "companies", ["county"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255)),
        sa.Column("google_id", sa.String(255), unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", user_role, nullable=False, server_default="student"),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL")),
        sa.Column("county", sa.String(100)),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("password_hash IS NOT NULL OR google_id IS NOT NULL", name="chk_auth_method"),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", opportunity_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text()),
        sa.Column("responsibilities", sa.Text()),
        sa.Column("county", sa.String(100)),
        sa.Column("town", sa.String(100)),
        sa.Column("is_remote", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_hybrid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stipend_amount", sa.Numeric(10, 2)),
        sa.Column("application_deadline", sa.Date()),
        sa.Column("external_url", sa.String(500)),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("status", opportunity_status, nullable=False, server_default="active"),
        sa.Column("search_vector", postgresql.TSVECTOR()),
        sa.Column("scraped_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_opportunities_company", "opportunities", ["company_id"])
    op.create_index("idx_opportunities_type", "opportunities", ["type"])
    op.create_index("idx_opportunities_status", "opportunities", ["status"])
    op.create_index("idx_opportunities_county", "opportunities", ["county"])
    op.create_index("idx_opportunities_deadline", "opportunities", ["application_deadline"])
    op.create_index("idx_opportunities_search", "opportunities", ["search_vector"], postgresql_using="gin")

    op.execute(
        """
        CREATE FUNCTION opportunities_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(NEW.requirements, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_opportunities_search_vector
            BEFORE INSERT OR UPDATE ON opportunities
            FOR EACH ROW EXECUTE FUNCTION opportunities_search_vector_update();
        """
    )

    op.create_table(
        "opportunity_courses",
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "saved_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "opportunity_id", name="uq_saved_user_opportunity"),
    )

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template", sa.String(50), nullable=False, server_default="modern"),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("pdf_url", sa.String(500)),
        sa.Column("docx_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cover_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", payment_type, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("checkout_request_id", sa.String(100), unique=True),
        sa.Column("mpesa_receipt", sa.String(50)),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("cover_letter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cover_letters.id")),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payments.id")),
        sa.Column("status", application_status, nullable=False, server_default="pending_payment"),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "opportunity_id", name="uq_application_user_opportunity"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "company_id", name="uq_review_user_company"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_rating_range"),
    )

    op.create_table(
        "alert_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE")),
        sa.Column("county", sa.String(100)),
        sa.Column("industry", sa.String(120)),
        sa.Column("keyword", sa.String(150)),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("alert_subscriptions")
    op.drop_table("reviews")
    op.drop_table("applications")
    op.drop_table("payments")
    op.drop_table("cover_letters")
    op.drop_table("resumes")
    op.drop_table("saved_opportunities")
    op.drop_table("opportunity_courses")
    op.execute("DROP TRIGGER IF EXISTS trg_opportunities_search_vector ON opportunities")
    op.execute("DROP FUNCTION IF EXISTS opportunities_search_vector_update()")
    op.drop_table("opportunities")
    op.drop_table("users")
    op.drop_table("companies")
    op.drop_table("courses")

    bind = op.get_bind()
    for enum_name in (
        "payment_status",
        "payment_type",
        "application_status",
        "opportunity_status",
        "opportunity_type",
        "course_level",
        "user_role",
    ):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
