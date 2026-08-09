"""Import every model so Base.metadata is complete for Alembic."""
from app.models.alert_subscription import AlertSubscription
from app.models.application import Application
from app.models.company import Company
from app.models.cover_letter import CoverLetter
from app.models.course import Course
from app.models.opportunity import Opportunity, OpportunityCourse
from app.models.payment import Payment
from app.models.resume import Resume
from app.models.review import Review
from app.models.saved_opportunity import SavedOpportunity
from app.models.user import User

__all__ = [
    "AlertSubscription",
    "Application",
    "Company",
    "CoverLetter",
    "Course",
    "Opportunity",
    "OpportunityCourse",
    "Payment",
    "Resume",
    "Review",
    "SavedOpportunity",
    "User",
]
