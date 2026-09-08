# URO Research Monitoring Application — Implementation Plan

**Version:** 1.0
**Date:** 2026-09-07

---

## 1. Repository Assessment

### Current State
- **Repository is empty** — only contains documentation and design assets
- `/URO_Research_Monitoring_Application_PRD.md` — complete PRD (1473 lines)
- `/URO_UI_DESIGN_SPEC.md` — complete UI specification (880 lines)
- `/docs/` — contains 4 design assets:
  - `logo-circle(1).png` — HAU circular seal
  - `university_research_monitoring_dashboard.png` — Dashboard mockup
  - `research_projects_dashboard.png` — Research Projects mockup
  - `holy_angel_university_evaluators_dashboard.png` — Evaluators mockup
- No application code, no Docker files, no configuration files exist

### Decision
Build from scratch using the PRD-recommended architecture. No existing code to preserve.

---

## 2. Proposed Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React 18 + TypeScript + Vite | PRD-recommended, fast dev server |
| CSS | Tailwind CSS + shadcn/ui | PRD UI spec recommended |
| Icons | Lucide React | PRD UI spec recommended |
| Charts | Recharts | PRD UI spec recommended |
| Backend | Python 3.12 + FastAPI | PRD-recommended |
| ORM | SQLAlchemy 2.0 | PRD-recommended |
| Migrations | Alembic | PRD-recommended |
| Validation | Pydantic v2 | PRD-recommended |
| Database | PostgreSQL 16 | PRD-recommended |
| Object Storage | Docker volume (dev), MinIO-ready | PRD-recommended |
| Auth | JWT (python-jose) + bcrypt | NFR-001 |
| Container Runtime | Docker Compose | PRD requirement |

---

## 3. Docker Architecture

### Phase 1 Services (Minimum)

```yaml
services:
  frontend:     # React SPA served by Nginx
  api:          # FastAPI application
  db:           # PostgreSQL 16
```

### Phase 2+ Services (Planned)

```yaml
services:
  reverse-proxy:  # Nginx
  frontend:       # React SPA
  api:            # FastAPI
  worker:         # Background tasks (optional)
  redis:          # Caching/queues (optional)
  db:             # PostgreSQL
  object-storage: # MinIO (optional)
```

### Volumes
- `pgdata` — PostgreSQL persistent data
- `uploads` — Document/file persistent storage

### Ports (Development)
- Frontend: `${FRONTEND_PORT:-5173}`
- API: `${API_PORT:-8000}`
- PostgreSQL: `${DB_PORT:-5432}`

---

## 4. Database / Domain Model

### Identity & Organization
- `users` — id, email, password_hash, first_name, last_name, is_active, created_at, updated_at
- `roles` — id, name (RESEARCHER, DEAN, URO_STAFF, URO_DIRECTOR, EXTERNAL_EVALUATOR, IRB_REVIEWER, FINAL_EVALUATOR, ADMIN)
- `user_roles` — user_id, role_id
- `school_colleges` — id, name, code
- `department_units` — id, name, code, school_college_id
- `user_affiliations` — user_id, department_unit_id

### Research
- `research` — id, tracking_number, title, lead_proponent_id, status, academic_year_id, nature_of_research, target_journal, research_agenda, is_continuation, continuation_ref, created_by, created_at, updated_at
- `research_authors` — id, research_id, user_id (nullable for external), name, affiliation, mobile, email, contribution_pct, is_lead
- `research_declarations` — id, research_id, declaration_type, consent, consented_by, consented_at
- `research_readiness` — id, research_id, ready_for_presentation, ready_for_publication, marked_by, marked_at

### Documents
- `research_documents` — id, research_id, document_type, created_at
- `research_document_versions` — id, document_id, version_number, original_filename, stored_filename, mime_type, file_size, uploaded_by, uploaded_at, workflow_stage, reason, checksum, is_active

### Workflow
- `research_status_history` — id, research_id, prior_status, new_status, action, actor_id, actor_role, document_version_id, remarks, created_at
- `workflow_deadlines` — id, research_id, stage, assigned_at, due_at, completed_at, is_overdue, reminders_sent

### Turnitin
- `similarity_check_attempts` — id, research_id, document_version_id, stage (PROPOSAL/FINAL_PAPER), similarity_score, threshold_at_decision, result (ACCEPTABLE/REVISION_REQUIRED), report_file, annotations, recorded_by, recorded_at

### Evaluation
- `evaluator_profiles` — id, user_id, expertise, is_active
- `evaluation_assignments` — id, research_id, evaluator_id, evaluation_type (PROPOSAL/FINAL), status, round_number, document_version_id, assigned_at, accepted_at, declined_at, completed_at
- `evaluation_submissions` — id, assignment_id, document_version_id, score, pass_fail, comments, recommendation, submitted_at, submitted_by

### IRB
- `irb_reviews` — id, research_id, document_version_id, reviewer_id, decision (REVISION_REQUIRED/NOT_APPROVED/APPROVED), comments, decided_at, round_number

### Implementation
- `research_milestones` — id, research_id, activity, target_start, target_end, actual_start, actual_end, status, remarks, evidence_document_id

### Notifications
- `notifications` — id, user_id, research_id, type, title, message, is_read, created_at

### Audit
- `audit_events` — id, research_id, event_type, actor_id, actor_role, details (JSONB), created_at

### Configurable Settings
- `system_settings` — id, key, value, updated_by, updated_at

---

## 5. Application Modules

### Backend API Structure

```
backend/
├── alembic/              # Database migrations
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry
│   ├── config.py         # Settings via pydantic-settings
│   ├── database.py       # SQLAlchemy engine/session
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── research.py
│   │   ├── document.py
│   │   ├── workflow.py
│   │   ├── evaluation.py
│   │   ├── turnitin.py
│   │   ├── irb.py
│   │   ├── notification.py
│   │   └── audit.py
│   ├── schemas/          # Pydantic request/response
│   ├── api/              # Route handlers
│   │   ├── auth.py
│   │   ├── research.py
│   │   ├── documents.py
│   │   ├── workflow.py
│   │   ├── evaluations.py
│   │   ├── turnitin.py
│   │   ├── irb.py
│   │   ├── admin.py
│   │   └── health.py
│   ├── services/         # Business logic
│   │   ├── auth.py
│   │   ├── workflow_engine.py
│   │   ├── document_service.py
│   │   └── evaluation_service.py
│   ├── middleware/
│   ├── security/         # JWT, password hashing, RBAC
│   └── utils/
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Frontend Structure

```
frontend/
├── src/
│   ├── assets/           # Logo, images
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── layout/       # AppShell, Sidebar, TopBar
│   │   ├── dashboard/    # Dashboard-specific components
│   │   └── shared/       # Reusable components
│   ├── pages/
│   ├── hooks/
│   ├── services/         # API client
│   ├── stores/           # State management
│   ├── types/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── Dockerfile
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

---

## 6. Workflow / State Machine Design

### Research Statuses (Enum)

```
DRAFT
SUBMITTED
FOR_DEAN_ENDORSEMENT
ENDORSED_TO_URO
INITIAL_EVALUATION
INITIAL_EVALUATION_REVISION_REQUIRED
PROPOSAL_TURNITIN
PROPOSAL_TURNITIN_REVISION_REQUIRED
PROPOSAL_TURNITIN_PASSED
EXTERNAL_EVALUATION
EXTERNAL_EVALUATION_REVISION_REQUIRED
SELECTIVE_EXTERNAL_REEVALUATION
EXTERNAL_EVALUATION_PASSED
FOR_IRB_REVIEW
IRB_REVISION_REQUIRED
PROPOSAL_APPROVED
RESEARCH_IN_PROGRESS
FINAL_PAPER_DUE
FINAL_PAPER_SUBMITTED
FINAL_PAPER_TURNITIN
FINAL_PAPER_TURNITIN_REVISION_REQUIRED
FINAL_PAPER_TURNITIN_PASSED
FINAL_BLIND_EVALUATION
FINAL_EVALUATION_REVISION_REQUIRED
SELECTIVE_FINAL_REEVALUATION
FINAL_BLIND_EVALUATION_PASSED
COMPLETED
READY_FOR_PRESENTATION
READY_FOR_PUBLICATION
ARCHIVED
```

### Transition Rules (Key Examples)

| From | To | Action | Guard |
|------|-----|--------|-------|
| DRAFT | SUBMITTED | submit | mandatory fields complete |
| SUBMITTED | FOR_DEAN_ENDORSEMENT | route | system |
| FOR_DEAN_ENDORSEMENT | ENDORSED_TO_URO | endorse | Dean action |
| FOR_DEAN_ENDORSEMENT | DRAFT | return | Dean returns with remarks |
| INITIAL_EVALUATION | INITIAL_EVALUATION_REVISION_REQUIRED | request_revision | URO action |
| INITIAL_EVALUATION | PROPOSAL_TURNITIN | pass | URO passes |
| PROPOSAL_TURNITIN | PROPOSAL_TURNITIN_PASSED | record_acceptable | URO records Turnitin result |
| PROPOSAL_TURNITIN | PROPOSAL_TURNITIN_REVISION_REQUIRED | record_revision | URO records unacceptable |
| PROPOSAL_TURNITIN_PASSED | EXTERNAL_EVALUATION | assign_evaluators | URO assigns |
| EXTERNAL_EVALUATION | SELECTIVE_EXTERNAL_REEVALUATION | selective_reevaluation | one evaluator failed |
| EXTERNAL_EVALUATION | EXTERNAL_EVALUATION_PASSED | all_passed | all evaluators pass |
| EXTERNAL_EVALUATION_PASSED | FOR_IRB_REVIEW | endorse_to_irb | URO action |
| FOR_IRB_REVIEW | PROPOSAL_APPROVED | approve | IRB approves |
| PROPOSAL_APPROVED | RESEARCH_IN_PROGRESS | begin_implementation | researcher starts |
| RESEARCH_IN_PROGRESS | FINAL_PAPER_SUBMITTED | submit_final_paper | researcher submits |
| FINAL_PAPER_SUBMITTED | FINAL_PAPER_TURNITIN | record_turnitin | URO records |
| FINAL_PAPER_TURNITIN_PASSED | FINAL_BLIND_EVALUATION | assign_final_evaluators | URO assigns |
| FINAL_BLIND_EVALUATION | SELECTIVE_FINAL_REEVALUATION | selective_reevaluation | one evaluator failed |
| FINAL_BLIND_EVALUATION | FINAL_BLIND_EVALUATION_PASSED | all_passed | all evaluators pass |
| FINAL_BLIND_EVALUATION_PASSED | COMPLETED | mark_completed | completion guard |
| COMPLETED | READY_FOR_PRESENTATION | set_presentation | authorized action |
| COMPLETED | READY_FOR_PUBLICATION | set_publication | authorized action |

---

## 7. Implementation Phases

### Phase 1 — Foundation (Current)
- [ ] Docker Compose with frontend, api, db
- [ ] Backend FastAPI application shell
- [ ] Frontend React application shell
- [ ] PostgreSQL connection and initial models
- [ ] Alembic migration setup
- [ ] Health endpoint
- [ ] Environment configuration
- [ ] .env.example
- [ ] README

### Phase 2 — Authentication & RBAC
- [ ] JWT authentication
- [ ] Password hashing
- [ ] Role-based access control
- [ ] Seed users for all roles
- [ ] Login/logout API

### Phase 3 — Organizational Structure
- [ ] Schools/colleges CRUD
- [ ] Departments/units CRUD
- [ ] User affiliations
- [ ] Academic years
- [ ] Research categories

### Phase 4 — Research Submission
- [ ] Research creation (draft)
- [ ] Co-author management
- [ ] Declarations
- [ ] Document upload with versioning
- [ ] Submission workflow
- [ ] Researcher dashboard

### Phase 5 — Document Versioning
- [ ] Version management
- [ ] File storage
- [ ] Version history
- [ ] Metadata tracking

### Phase 6 — Workflow Engine
- [ ] Centralized state machine
- [ ] Transition guards
- [ ] Audit trail
- [ ] Status history

### Phase 7 — Dean Endorsement
- [ ] Endorse/return workflow
- [ ] Routing based on affiliation
- [ ] Remarks on return

### Phase 8 — Initial URO Evaluation
- [ ] Initial evaluation
- [ ] Pass/revision cycle
- [ ] URO dashboard

### Phase 9 — Proposal Turnitin
- [ ] Turnitin attempt recording
- [ ] Threshold configuration
- [ ] Revision loop

### Phase 10 — External Evaluation
- [ ] Evaluator assignment
- [ ] Invitation accept/decline
- [ ] Replacement assignment
- [ ] Independent evaluations
- [ ] Selective re-evaluation

### Phase 11 — IRB
- [ ] IRB routing
- [ ] Decision recording
- [ ] Revision loop
- [ ] Proposal approval

### Phase 12 — Implementation Monitoring
- [ ] Milestones
- [ ] Timeline/Gantt data
- [ ] Progress tracking

### Phase 13 — Final Paper
- [ ] Final paper submission
- [ ] Versioning

### Phase 14 — Final Paper Turnitin
- [ ] Final Turnitin recording
- [ ] Gating before blind evaluation
- [ ] Revision loop

### Phase 15 — Final Blind Evaluation
- [ ] Blind evaluator assignment
- [ ] Independent outcomes
- [ ] Selective re-evaluation
- [ ] Completion guard

### Phase 16 — Completion & Reporting
- [ ] Completion flag
- [ ] Presentation/publication readiness
- [ ] Archive
- [ ] Reports

---

## 8. Testing Strategy

### Unit Tests
- Workflow state machine transitions
- Validation logic
- Service layer functions

### Integration Tests
- API endpoint behavior
- Authentication/authorization
- Document versioning
- Evaluation workflows

### Critical Test Cases (from PRD §26)
1. Researcher can create draft
2. Cannot bypass Dean endorsement
3. Initial revision creates new version
4. External evaluation gated by Turnitin
5. Proposal Turnitin revision loop
6. Declined evaluator replacement
7. Independent evaluator results
8. Selective proposal re-evaluation (one fail)
9. Selective proposal re-evaluation (both fail)
10. IRB approval → implementation, not completed
11. Final paper submission after implementation
12. Final blind evaluation gated by final Turnitin
13. Final Turnitin revision loop
14. Selective final re-evaluation (one fail)
15. Selective final re-evaluation (both fail)
16. Passing evaluator result preserved
17. Completed impossible before final blind pass
18. Completed set after all pass
19. Independent presentation/publication readiness
20. Audit trail records all transitions
21. Unauthorized roles blocked
22. Persistent data survives restart

---

## 9. Security Considerations

- Password hashing with bcrypt (NFR-001)
- JWT with configurable expiry
- Server-side RBAC on every endpoint
- Object-level access control
- File upload validation (type, size)
- Path traversal protection
- CSRF protection
- Login rate limiting
- CORS configuration
- No secrets in source control
- Environment-based configuration
- Structured logging

---

## 10. Assumptions / Open Issues

1. **Turnitin API** — v1 records results manually; API integration deferred
2. **Email notifications** — v1 in-app only; email config ready but not wired
3. **Redis** — deferred to Phase 2+ unless needed
4. **MinIO** — deferred; Docker volume for dev file storage
5. **PDF generation** — deferred; CSV export first
6. **E-signature** — out of scope per PRD
7. **Blind evaluation** — evaluator sees document without researcher metadata; URO sees all
8. **Configurable thresholds** — stored in system_settings table
9. **SLA deadlines** — configurable per stage, stored in system_settings
10. **Academic year format** — "2025-2026" as string identifier
