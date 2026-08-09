"""Enum types shared across models — string-valued so they serialize cleanly in JSON."""
import enum


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Pass to SQLAlchemy's Enum(..., values_callable=enum_values) on every enum column.

    Without this, SQLAlchemy sends each member's NAME ("STUDENT") to Postgres instead of
    its VALUE ("student"), which doesn't match the lowercase labels the migration creates.
    """
    return [member.value for member in enum_cls]


class UserRole(str, enum.Enum):
    STUDENT = "student"
    MODERATOR = "moderator"
    ADMIN = "admin"


class CourseLevel(str, enum.Enum):
    CERTIFICATE = "certificate"
    DIPLOMA = "diploma"
    DEGREE = "degree"
    POSTGRADUATE = "postgraduate"


class OpportunityType(str, enum.Enum):
    ATTACHMENT = "attachment"
    INTERNSHIP = "internship"
    GRADUATE_PROGRAM = "graduate_program"
    APPRENTICESHIP = "apprenticeship"


class OpportunityStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FILLED = "filled"
    FLAGGED = "flagged"


class ApplicationStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    SUBMITTED = "submitted"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentType(str, enum.Enum):
    APPLICATION_FEE = "application_fee"
    DONATION = "donation"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
