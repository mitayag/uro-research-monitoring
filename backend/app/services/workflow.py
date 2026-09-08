"""
Workflow state machine for URO Research Monitoring System.

Defines all valid state transitions and enforces business rules:
- No manual status changes allowed
- Turnitin gating (Proposal Turnitin before External Evaluation)
- Turnitin gating (Final Paper Turnitin before Final Blind Evaluation)
- Selective re-evaluation support
- Completion guard
- Separate presentation/publication flags
"""
from typing import Optional
from app.models.research import ResearchStatus


# Valid transitions: (source_status, action) -> target_status
# Action names match the PRD workflow rules
VALID_TRANSITIONS: dict[tuple[ResearchStatus, str], ResearchStatus] = {
    # === PHASE 1: Submission & Initial Processing ===
    (ResearchStatus.DRAFT, "SUBMIT"): ResearchStatus.SUBMITTED,
    (ResearchStatus.SUBMITTED, "FORWARD_TO_DEAN"): ResearchStatus.FOR_DEAN_ENDORSEMENT,
    (ResearchStatus.FOR_DEAN_ENDORSEMENT, "DEAN_ENDORSE"): ResearchStatus.ENDORSED_TO_URO,
    (ResearchStatus.FOR_DEAN_ENDORSEMENT, "DEAN_REJECT"): ResearchStatus.DRAFT,

    # === PHASE 2: URO Receipt & Initial Review ===
    (ResearchStatus.ENDORSED_TO_URO, "RECEIVE_BY_URO"): ResearchStatus.URO_RECEIVED,
    (ResearchStatus.URO_RECEIVED, "BEGIN_INITIAL_REVIEW"): ResearchStatus.INITIAL_REVIEW,
    (ResearchStatus.INITIAL_REVIEW, "INITIAL_REVIEW_PASS"): ResearchStatus.INITIAL_REVIEW_PASSED,
    (ResearchStatus.INITIAL_REVIEW, "INITIAL_REVIEW_REVISION"): ResearchStatus.INITIAL_REVISION_REQUIRED,
    (ResearchStatus.INITIAL_REVISION_REQUIRED, "RESUBMIT_INITIAL_REVISION"): ResearchStatus.INITIAL_REVISION_SUBMITTED,
    (ResearchStatus.INITIAL_REVISION_SUBMITTED, "BEGIN_INITIAL_REVIEW"): ResearchStatus.INITIAL_REVIEW,

    # === PHASE 3: Proposal Turnitin ===
    (ResearchStatus.INITIAL_REVIEW_PASSED, "BEGIN_PROPOSAL_TURNITIN"): ResearchStatus.PROPOSAL_TURNITIN,
    (ResearchStatus.PROPOSAL_TURNITIN, "TURNITIN_PASSED"): ResearchStatus.PROPOSAL_TURNITIN_PASSED,
    (ResearchStatus.PROPOSAL_TURNITIN, "TURNITIN_REVISION"): ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED,
    (ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED, "RESUBMIT_TURNITIN_REVISION"): ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED,
    (ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED, "BEGIN_PROPOSAL_TURNITIN"): ResearchStatus.PROPOSAL_TURNITIN,
    (ResearchStatus.PROPOSAL_TURNITIN_PASSED, "READY_FOR_EXTERNAL_EVAL"): ResearchStatus.READY_FOR_EXTERNAL_EVALUATION,

    # === PHASE 4: External Evaluation ===
    (ResearchStatus.READY_FOR_EXTERNAL_EVALUATION, "BEGIN_EXTERNAL_EVAL"): ResearchStatus.EXTERNAL_EVALUATION,
    (ResearchStatus.EXTERNAL_EVALUATION, "EXTERNAL_EVAL_PASS"): ResearchStatus.EXTERNAL_EVALUATION_PASSED,
    (ResearchStatus.EXTERNAL_EVALUATION, "EXTERNAL_EVAL_REVISION"): ResearchStatus.EXTERNAL_EVALUATION_REVISION_REQUIRED,
    (ResearchStatus.EXTERNAL_EVALUATION_REVISION_REQUIRED, "RESUBMIT_AFTER_EXTERNAL_REVISION"): ResearchStatus.SELECTIVE_EXTERNAL_REEVALUATION,
    (ResearchStatus.SELECTIVE_EXTERNAL_REEVALUATION, "SELECTIVE_REEVAL_PASS"): ResearchStatus.EXTERNAL_EVALUATION_PASSED,
    (ResearchStatus.SELECTIVE_EXTERNAL_REEVALUATION, "SELECTIVE_REEVAL_FAIL"): ResearchStatus.EXTERNAL_EVALUATION_REVISION_REQUIRED,
    (ResearchStatus.EXTERNAL_EVALUATION_PASSED, "FORWARD_TO_IRB"): ResearchStatus.FOR_IRB_REVIEW,

    # === PHASE 5: IRB Review ===
    (ResearchStatus.FOR_IRB_REVIEW, "IRB_APPROVE"): ResearchStatus.PROPOSAL_APPROVED,
    (ResearchStatus.FOR_IRB_REVIEW, "IRB_REVISION"): ResearchStatus.IRB_REVISION_REQUIRED,
    (ResearchStatus.IRB_REVISION_REQUIRED, "RESUBMIT_AFTER_IRB_REVISION"): ResearchStatus.FOR_IRB_REVIEW,
    (ResearchStatus.FOR_IRB_REVIEW, "IRB_NOT_APPROVED"): ResearchStatus.IRB_REVISION_REQUIRED,
    (ResearchStatus.PROPOSAL_APPROVED, "BEGIN_RESEARCH"): ResearchStatus.RESEARCH_IN_PROGRESS,

    # === PHASE 6: Research Execution ===
    (ResearchStatus.RESEARCH_IN_PROGRESS, "SUBMIT_FINAL_PAPER"): ResearchStatus.FINAL_PAPER_SUBMITTED,
    (ResearchStatus.FINAL_PAPER_DUE, "SUBMIT_FINAL_PAPER"): ResearchStatus.FINAL_PAPER_SUBMITTED,

    # === PHASE 7: Final Paper Turnitin (Gating) ===
    (ResearchStatus.FINAL_PAPER_SUBMITTED, "BEGIN_FINAL_TURNITIN"): ResearchStatus.FINAL_PAPER_TURNITIN,
    (ResearchStatus.FINAL_PAPER_TURNITIN, "FINAL_TURNITIN_PASSED"): ResearchStatus.FINAL_PAPER_TURNITIN_PASSED,
    (ResearchStatus.FINAL_PAPER_TURNITIN, "FINAL_TURNITIN_REVISION"): ResearchStatus.FINAL_PAPER_TURNITIN_REVISION_REQUIRED,
    (ResearchStatus.FINAL_PAPER_TURNITIN_REVISION_REQUIRED, "RESUBMIT_AFTER_FINAL_TURNITIN"): ResearchStatus.FINAL_PAPER_TURNITIN,
    (ResearchStatus.FINAL_PAPER_TURNITIN_PASSED, "FORWARD_TO_FINAL_EVAL"): ResearchStatus.FINAL_BLIND_EVALUATION,

    # === PHASE 8: Final Blind Evaluation ===
    (ResearchStatus.FINAL_BLIND_EVALUATION, "FINAL_EVAL_PASS"): ResearchStatus.FINAL_BLIND_EVALUATION_PASSED,
    (ResearchStatus.FINAL_BLIND_EVALUATION, "FINAL_EVAL_REVISION"): ResearchStatus.FINAL_EVALUATION_REVISION_REQUIRED,
    (ResearchStatus.FINAL_EVALUATION_REVISION_REQUIRED, "RESUBMIT_AFTER_FINAL_REVISION"): ResearchStatus.SELECTIVE_FINAL_REEVALUATION,
    (ResearchStatus.SELECTIVE_FINAL_REEVALUATION, "SELECTIVE_FINAL_REEVAL_PASS"): ResearchStatus.FINAL_BLIND_EVALUATION_PASSED,
    (ResearchStatus.SELECTIVE_FINAL_REEVALUATION, "SELECTIVE_FINAL_REEVAL_FAIL"): ResearchStatus.FINAL_EVALUATION_REVISION_REQUIRED,
    (ResearchStatus.FINAL_BLIND_EVALUATION_PASSED, "MARK_COMPLETED"): ResearchStatus.COMPLETED,

    # === PHASE 9: Completion & Post-Completion ===
    (ResearchStatus.COMPLETED, "MARK_READY_PRESENTATION"): ResearchStatus.READY_FOR_PRESENTATION,
    (ResearchStatus.COMPLETED, "MARK_READY_PUBLICATION"): ResearchStatus.READY_FOR_PUBLICATION,
    (ResearchStatus.READY_FOR_PRESENTATION, "MARK_READY_PUBLICATION"): ResearchStatus.READY_FOR_PUBLICATION,
    (ResearchStatus.READY_FOR_PUBLICATION, "MARK_READY_PRESENTATION"): ResearchStatus.READY_FOR_PRESENTATION,
    (ResearchStatus.READY_FOR_PRESENTATION, "ARCHIVE"): ResearchStatus.ARCHIVED,
    (ResearchStatus.READY_FOR_PUBLICATION, "ARCHIVE"): ResearchStatus.ARCHIVED,
    (ResearchStatus.COMPLETED, "ARCHIVE"): ResearchStatus.ARCHIVED,
}


def get_valid_actions(current_status: ResearchStatus) -> list[str]:
    """Return list of actions available from the given status."""
    return [
        action
        for (src, action), _ in VALID_TRANSITIONS.items()
        if src == current_status
    ]


def can_transition(current_status: ResearchStatus, action: str) -> bool:
    """Check if a transition is valid."""
    return (current_status, action) in VALID_TRANSITIONS


def get_target_status(current_status: ResearchStatus, action: str) -> Optional[ResearchStatus]:
    """Get the target status for a valid action."""
    return VALID_TRANSITIONS.get((current_status, action))


# Role-based action permissions
# Maps actions to the roles that can perform them
ACTION_ROLE_PERMISSIONS: dict[str, list[str]] = {
    # Submission
    "SUBMIT": ["RESEARCHER", "ADMIN"],
    "FORWARD_TO_DEAN": ["RESEARCHER", "ADMIN"],
    "DEAN_ENDORSE": ["DEAN", "ADMIN"],
    "DEAN_REJECT": ["DEAN", "ADMIN"],

    # URO Receipt & Initial Review
    "RECEIVE_BY_URO": ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
    "BEGIN_INITIAL_REVIEW": ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
    "INITIAL_REVIEW_PASS": ["URO_DIRECTOR", "ADMIN"],
    "INITIAL_REVIEW_REVISION": ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
    "RESUBMIT_INITIAL_REVISION": ["RESEARCHER", "ADMIN"],

    # Proposal Turnitin
    "BEGIN_PROPOSAL_TURNITIN": ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
    "TURNITIN_PASSED": ["URO_DIRECTOR", "ADMIN"],
    "TURNITIN_REVISION": ["URO_DIRECTOR", "URO_STAFF", "ADMIN"],
    "RESUBMIT_TURNITIN_REVISION": ["RESEARCHER", "ADMIN"],
    "READY_FOR_EXTERNAL_EVAL": ["URO_DIRECTOR", "ADMIN"],

    # External Evaluation
    "BEGIN_EXTERNAL_EVAL": ["URO_DIRECTOR", "ADMIN"],
    "EXTERNAL_EVAL_PASS": ["URO_DIRECTOR", "ADMIN"],
    "EXTERNAL_EVAL_REVISION": ["URO_DIRECTOR", "ADMIN"],
    "RESUBMIT_AFTER_EXTERNAL_REVISION": ["RESEARCHER", "ADMIN"],
    "SELECTIVE_REEVAL_PASS": ["URO_DIRECTOR", "ADMIN"],
    "SELECTIVE_REEVAL_FAIL": ["URO_DIRECTOR", "ADMIN"],
    "FORWARD_TO_IRB": ["URO_DIRECTOR", "ADMIN"],

    # IRB
    "IRB_APPROVE": ["IRB_REVIEWER", "ADMIN"],
    "IRB_REVISION": ["IRB_REVIEWER", "ADMIN"],
    "IRB_NOT_APPROVED": ["IRB_REVIEWER", "ADMIN"],
    "RESUBMIT_AFTER_IRB_REVISION": ["RESEARCHER", "ADMIN"],
    "BEGIN_RESEARCH": ["RESEARCHER", "ADMIN"],

    # Final Paper
    "SUBMIT_FINAL_PAPER": ["RESEARCHER", "ADMIN"],
    "BEGIN_FINAL_TURNITIN": ["URO_DIRECTOR", "ADMIN"],
    "FINAL_TURNITIN_PASSED": ["URO_DIRECTOR", "ADMIN"],
    "FINAL_TURNITIN_REVISION": ["URO_DIRECTOR", "ADMIN"],
    "RESUBMIT_AFTER_FINAL_TURNITIN": ["RESEARCHER", "ADMIN"],
    "FORWARD_TO_FINAL_EVAL": ["URO_DIRECTOR", "ADMIN"],

    # Final Evaluation
    "FINAL_EVAL_PASS": ["URO_DIRECTOR", "ADMIN"],
    "FINAL_EVAL_REVISION": ["URO_DIRECTOR", "ADMIN"],
    "RESUBMIT_AFTER_FINAL_REVISION": ["RESEARCHER", "ADMIN"],
    "SELECTIVE_FINAL_REEVAL_PASS": ["URO_DIRECTOR", "ADMIN"],
    "SELECTIVE_FINAL_REEVAL_FAIL": ["URO_DIRECTOR", "ADMIN"],
    "MARK_COMPLETED": ["URO_DIRECTOR", "ADMIN"],

    # Post-Completion
    "MARK_READY_PRESENTATION": ["URO_DIRECTOR", "ADMIN"],
    "MARK_READY_PUBLICATION": ["URO_DIRECTOR", "ADMIN"],
    "ARCHIVE": ["ADMIN"],
}


def can_user_perform_action(user_roles: list[str], action: str) -> bool:
    """Check if a user's roles allow them to perform a given action."""
    allowed_roles = ACTION_ROLE_PERMISSIONS.get(action, [])
    return any(role in allowed_roles for role in user_roles)


# Category labels for grouping statuses in the UI
STATUS_CATEGORIES = {
    "submission": {
        "label": "Submission & Initial Processing",
        "statuses": [
            ResearchStatus.DRAFT,
            ResearchStatus.SUBMITTED,
            ResearchStatus.FOR_DEAN_ENDORSEMENT,
            ResearchStatus.ENDORSED_TO_URO,
        ],
    },
    "initial_review": {
        "label": "URO Receipt & Initial Review",
        "statuses": [
            ResearchStatus.URO_RECEIVED,
            ResearchStatus.INITIAL_REVIEW,
            ResearchStatus.INITIAL_REVISION_REQUIRED,
            ResearchStatus.INITIAL_REVISION_SUBMITTED,
            ResearchStatus.INITIAL_REVIEW_PASSED,
        ],
    },
    "turnitin_proposal": {
        "label": "Proposal Turnitin Check",
        "statuses": [
            ResearchStatus.PROPOSAL_TURNITIN,
            ResearchStatus.PROPOSAL_TURNITIN_REVISION_REQUIRED,
            ResearchStatus.PROPOSAL_TURNITIN_RESUBMITTED,
            ResearchStatus.PROPOSAL_TURNITIN_PASSED,
        ],
    },
    "external_eval": {
        "label": "External Evaluation",
        "statuses": [
            ResearchStatus.READY_FOR_EXTERNAL_EVALUATION,
            ResearchStatus.EXTERNAL_EVALUATION,
            ResearchStatus.EXTERNAL_EVALUATION_REVISION_REQUIRED,
            ResearchStatus.SELECTIVE_EXTERNAL_REEVALUATION,
            ResearchStatus.EXTERNAL_EVALUATION_PASSED,
        ],
    },
    "irb": {
        "label": "IRB Review",
        "statuses": [
            ResearchStatus.FOR_IRB_REVIEW,
            ResearchStatus.IRB_REVISION_REQUIRED,
            ResearchStatus.PROPOSAL_APPROVED,
        ],
    },
    "research": {
        "label": "Research Execution",
        "statuses": [
            ResearchStatus.RESEARCH_IN_PROGRESS,
            ResearchStatus.FINAL_PAPER_DUE,
            ResearchStatus.FINAL_PAPER_SUBMITTED,
        ],
    },
    "turnitin_final": {
        "label": "Final Paper Turnitin Check",
        "statuses": [
            ResearchStatus.FINAL_PAPER_TURNITIN,
            ResearchStatus.FINAL_PAPER_TURNITIN_REVISION_REQUIRED,
            ResearchStatus.FINAL_PAPER_TURNITIN_PASSED,
        ],
    },
    "final_eval": {
        "label": "Final Blind Evaluation",
        "statuses": [
            ResearchStatus.FINAL_BLIND_EVALUATION,
            ResearchStatus.FINAL_EVALUATION_REVISION_REQUIRED,
            ResearchStatus.SELECTIVE_FINAL_REEVALUATION,
            ResearchStatus.FINAL_BLIND_EVALUATION_PASSED,
        ],
    },
    "completion": {
        "label": "Completion & Post-Completion",
        "statuses": [
            ResearchStatus.COMPLETED,
            ResearchStatus.READY_FOR_PRESENTATION,
            ResearchStatus.READY_FOR_PUBLICATION,
            ResearchStatus.ARCHIVED,
        ],
    },
}
