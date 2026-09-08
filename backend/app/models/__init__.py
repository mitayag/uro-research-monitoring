from app.models.user import User, Role, UserRole, SchoolCollege, DepartmentUnit, UserAffiliation
from app.models.research import (
    Research,
    ResearchAuthor,
    ResearchDeclaration,
    ResearchReadiness,
    ResearchStatusHistory,
    AcademicYear,
)
from app.models.document import ResearchDocument, ResearchDocumentVersion
from app.models.evaluation import (
    EvaluatorProfile,
    EvaluationAssignment,
    EvaluationSubmission,
)
from app.models.turnitin import SimilarityCheckAttempt
from app.models.initial_review import InitialReview, InitialReviewItem
from app.models.irb import IRBReview
from app.models.milestone import ResearchMilestone
from app.models.notification import Notification
from app.models.audit import AuditEvent
from app.models.settings import SystemSetting

__all__ = [
    "User", "Role", "UserRole",
    "Research", "ResearchAuthor", "ResearchDeclaration",
    "ResearchReadiness", "ResearchStatusHistory",
    "AcademicYear", "SchoolCollege", "DepartmentUnit", "UserAffiliation",
    "ResearchDocument", "ResearchDocumentVersion",
    "EvaluatorProfile", "EvaluationAssignment", "EvaluationSubmission",
    "SimilarityCheckAttempt",
    "InitialReview", "InitialReviewItem",
    "IRBReview",
    "ResearchMilestone",
    "Notification",
    "AuditEvent",
    "SystemSetting",
]
