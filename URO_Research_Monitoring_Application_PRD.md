# Product Requirements Document (PRD)
## URO Research Monitoring Application

**Document Version:** 1.0  
**Date:** 2026-09-07  
**Primary Basis:** `URO_Research_Monitoring_Program_Flows_Revised_v3`  
**Deployment Requirement:** Docker containers  
**Intended Consumer:** AI coding harness / software development agent  
**Product Type:** Internal web application for monitoring research submissions through the University Research Office (URO) review lifecycle

---

# 1. Purpose

The URO Research Monitoring Application is a workflow-driven web application that monitors a research submission from initial drafting and endorsement through proposal review, Turnitin checking, external evaluation, Institutional Review Board (IRB) review, research implementation, final-paper Turnitin checking, final blind evaluation, completion, presentation/publication readiness, and archival.

The application is not merely a document repository. The workflow engine is the system of record. Every status change must result from a valid user/system action, must be auditable, and must preserve prior versions, reviewer decisions, comments, timestamps, and assignments.

The system must make it possible to answer, for every research submission:

- Where is the research now?
- Who currently has responsibility for the next action?
- How long has it been in the current stage?
- What actions and decisions occurred previously?
- What document version was reviewed at each stage?
- Which evaluator(s) passed or failed the submission?
- Which evaluator(s) must perform a selective re-evaluation?
- Is the submission overdue?
- Is the research already eligible to be tagged Completed?
- Is the completed research ready for presentation and/or publication?

---

# 2. Product Goals

1. Digitize and monitor the complete URO research review workflow.
2. Prevent manual or arbitrary workflow status changes.
3. Preserve complete document version history.
4. Support repeated revision cycles at defined review stages.
5. Support proposal Turnitin checking and final-paper Turnitin checking.
6. Support individual evaluator outcomes and selective re-evaluation.
7. Support final blind evaluation before a research record can become Completed.
8. Give researchers clear visibility into current status, required action, deadlines, and history.
9. Give URO an operational dashboard for workload, pending items, overdue actions, and bottlenecks.
10. Run reproducibly in Docker containers.

---

# 3. Scope

## 3.1 In Scope

- Authentication and role-based access control
- Researcher profile and organizational affiliation
- New research submission
- Digital research application metadata
- Co-author management
- Document upload and versioning
- Dean / Unit / Department Head endorsement
- URO receipt and initial evaluation
- Proposal Turnitin result recording
- Proposal revision and Turnitin resubmission
- External evaluator assignment
- External evaluator invitation acceptance/decline
- Replacement evaluator assignment
- Individual evaluator scores/results/comments
- Selective external re-evaluation
- IRB review and revision loop
- Proposal approval
- Research implementation monitoring
- Milestone / timeline tracking
- Logistical support request tracking
- Final-paper submission
- Final-paper Turnitin result recording
- Final-paper Turnitin revision loop
- Final blind evaluator assignment
- Individual final evaluator outcomes
- Selective final re-evaluation
- Completion tagging only after final blind evaluation passes
- Presentation/publication readiness flags
- Notifications
- Deadline and overdue monitoring
- Audit trail
- Dashboards and reports
- Administration/configuration
- Dockerized deployment
- Backup-friendly persistent data volumes
- Automated tests

## 3.2 Out of Scope for Initial Release

Unless later specified, the AI harness must not implement these as mandatory integrations in v1:

- Automatic Turnitin API integration
- Automatic plagiarism/similarity scoring
- External journal submission integration
- ORCID integration
- Automatic publication indexing
- Payroll/accounting integration
- Automatic reimbursement/payment processing
- E-signature provider integration
- AI-generated evaluator ratings
- AI-generated approval decisions

The first release records Turnitin results and review decisions entered by authorized users. External integration points should be designed so they can be added later.

---

# 4. Source-of-Truth Workflow

The application must implement the following lifecycle.

## Phase A — Proposal Submission and Screening

1. Draft
2. Submitted
3. For Dean Endorsement
4. Endorsed to URO
5. Initial Evaluation
6. Initial Evaluation — Revision Required (repeatable)
7. Proposal Turnitin
8. Proposal Turnitin — Revision Required (repeatable)
9. Proposal Turnitin Passed

## Phase B — Proposal Review and Approval

10. External Evaluation
11. External Evaluation — Revision Required
12. Selective External Re-evaluation
13. External Evaluation Passed
14. For IRB Review
15. IRB — Revision Required
16. Proposal Approved

## Phase C — Implementation and Final Paper

17. Research In Progress
18. Final Paper Due
19. Final Paper Submitted
20. Final Paper Turnitin
21. Final Paper Turnitin — Revision Required
22. Final Paper Turnitin Passed
23. Final Blind Evaluation
24. Final Evaluation — Revision Required
25. Selective Final Re-evaluation
26. Final Blind Evaluation Passed
27. Completed
28. Ready for Presentation and/or Publication
29. Archived

Revision states are repeatable. Every resubmission creates a new version; it must not overwrite the prior version.

---

# 5. Mandatory Workflow Rules

These rules are non-negotiable unless changed by an approved later PRD.

## WF-001 — Workflow-driven status
Users must not directly type or arbitrarily set a research status. Status transitions must occur only through authorized workflow actions.

## WF-002 — Immutable history
Every transition must create an audit event containing at minimum:
- research ID
- prior status
- new status
- actor
- actor role
- action
- timestamp
- document version involved
- optional remarks

## WF-003 — Proposal revision
If initial evaluation requires revision, the researcher must submit a new proposal version. The previous file remains available to authorized users.

## WF-004 — Proposal Turnitin
A proposal that passes initial evaluation must undergo proposal Turnitin checking before external evaluation.

## WF-005 — Proposal Turnitin revision
If the proposal Turnitin result is not acceptable:
1. URO records annotations/remarks.
2. Status becomes `PROPOSAL_TURNITIN_REVISION_REQUIRED`.
3. Researcher submits a revised proposal version.
4. A new Turnitin attempt is created.
5. The loop repeats until an authorized URO user records an acceptable result.

The application must not hard-code a similarity percentage unless configured by an administrator. The threshold must be configurable.

## WF-006 — Two proposal external evaluators
The default external-evaluation workflow assigns two external evaluators.

## WF-007 — Invitation response
An evaluator may Accept or Decline.
- Accepted: evaluator may review the assigned version.
- Declined: URO assigns a replacement.
- Declined evaluators cannot submit an evaluation.

## WF-008 — Individual evaluator outcome
Each evaluator submission must contain an individual result, not only a calculated mean.

Minimum fields:
- evaluator
- evaluation round
- document version
- score/rating if used
- pass/fail outcome
- comments/recommendations
- submitted timestamp

## WF-009 — Selective proposal re-evaluation
If a revised proposal requires re-evaluation because one or more evaluators failed it:
- passing evaluator results remain valid;
- only evaluator(s) whose required outcome was failing are assigned the revised proposal for re-evaluation;
- if both failed, both receive re-evaluation assignments.

Do not force a passing evaluator to re-evaluate unless URO explicitly invalidates that evaluation through an administrative action with reason and audit record.

## WF-010 — IRB
Only a proposal that satisfies external evaluation requirements may proceed to IRB.

IRB outcomes:
- Revision Required
- Not Approved
- Approved

If Revision Required, a new version is submitted and routed back to IRB according to the configured policy.

IRB approval must not mark the research Completed.

## WF-011 — Proposal approval
IRB Approved transitions the research to `PROPOSAL_APPROVED`, after which implementation monitoring may begin.

## WF-012 — Implementation monitoring
Research implementation must support:
- target milestones
- actual dates
- progress status
- documents/evidence
- remarks
- logistical support information
- researcher updates
- URO monitoring

## WF-013 — Final paper submission
When research work is finished, the researcher submits a Final Paper as a versioned document.

## WF-014 — Final-paper Turnitin BEFORE final evaluation
The final paper must undergo Turnitin checking before it can be assigned for final blind evaluation.

Required sequence:

`FINAL_PAPER_SUBMITTED`
→ `FINAL_PAPER_TURNITIN`
→ either `FINAL_PAPER_TURNITIN_REVISION_REQUIRED` or `FINAL_PAPER_TURNITIN_PASSED`
→ only then `FINAL_BLIND_EVALUATION`

No final blind evaluator may receive a final paper that has not passed final-paper Turnitin.

## WF-015 — Final-paper Turnitin revision
If final-paper Turnitin is not acceptable:
1. URO records result and annotations.
2. Researcher revises and submits a new final-paper version.
3. A new final Turnitin attempt is created.
4. Repeat until accepted.

## WF-016 — Blind final evaluation
Final evaluation must be blind from the evaluator perspective where required by URO policy.

The application must support at least two final evaluators.

The evaluator-facing document package must not expose researcher-identifying metadata when blind mode is enabled.

## WF-017 — Individual final evaluator outcome
Each final evaluator must submit an independent pass/fail outcome and comments/recommendations.

## WF-018 — Selective final re-evaluation
If the final paper does not pass because only one evaluator gives a failing outcome:
1. URO consolidates the final-evaluation recommendations.
2. Researcher submits a revised final-paper version.
3. The passing evaluator's result remains valid.
4. Only the evaluator who gave the failing outcome receives the revised final paper for re-evaluation.

If both evaluators fail, both must receive re-evaluation assignments.

The system must keep all prior rounds and outcomes.

## WF-019 — Completion rule
The research may be tagged `COMPLETED` only when:
- final-paper Turnitin has passed; and
- all required final blind evaluator outcomes have passed.

Final-paper submission alone does not mean Completed.
IRB approval does not mean Completed.
Research implementation ending does not mean Completed.

## WF-020 — Presentation/publication readiness
After `COMPLETED`, the research may be tagged independently:
- Ready for Presentation
- Ready for Publication

These should be separate boolean/outcome flags so the record may be one, both, or neither.

## WF-021 — Archive
Archived records are read-only except for authorized administrative restoration or post-completion publication metadata updates.

---

# 6. User Roles and Permissions

## 6.1 Researcher / Scholar

Can:
- create a draft research submission
- edit own draft
- manage co-authors before submission
- upload proposal/final-paper versions
- submit research
- view workflow status
- view permitted comments/recommendations
- respond to revision requests
- submit milestone updates
- upload required evidence/documents
- view deadlines and notifications
- view own audit/timeline events relevant to the researcher

Cannot:
- approve own submission
- assign evaluators
- edit evaluator results
- mark own research Completed
- directly change workflow status

## 6.2 Dean / Principal / Unit / Department Head

Can:
- view submissions routed to their unit
- endorse
- return to researcher with remarks
- view relevant submission history

Cannot:
- perform URO evaluation unless separately assigned another role

## 6.3 Research Coordinator / URO Staff

Can:
- receive submissions
- validate completeness
- route work
- record Turnitin results when authorized
- manage documents and workflow administration
- monitor deadlines
- communicate revision requirements
- produce reports

## 6.4 URO Director

Can:
- perform/confirm initial evaluation
- assign/reassign evaluators
- invalidate an evaluator assignment/result with reason
- endorse to IRB
- approve configured URO actions
- manage exceptional workflow cases
- view full URO dashboard and reports

## 6.5 External Evaluator

Can:
- see only assigned submissions
- accept/decline invitation
- access the assigned document version
- submit rating/outcome/comments
- see own prior evaluation when re-evaluation is assigned

Cannot:
- see another evaluator's identity/result before permitted
- access unrelated research
- alter a submitted evaluation except through authorized reopen/revision action

## 6.6 IRB Reviewer / IRB Administrator

Can:
- see research routed to IRB
- review assigned version
- submit IRB decision and comments
- request revision

## 6.7 Final Blind Evaluator

Can:
- see only assigned blinded final-paper package
- submit independent result/comments
- perform selective re-evaluation if reassigned

Must not see researcher/co-author identity in the blinded package when blind mode is enabled.

## 6.8 System Administrator

Can:
- manage users and roles
- manage schools/colleges/departments/units
- configure workflow thresholds and SLA values
- manage research categories
- manage academic years
- manage notification templates
- manage system settings
- view system audit logs

Administrator access must not silently bypass audit rules.

---

# 7. Research Application Data

The new-submission module must support the application information currently represented by URO forms.

Minimum fields:

## Research Metadata
- Research ID / tracking number
- Proposal title
- Lead proponent
- HAU affiliation / unit
- mobile number
- institutional email
- nature of research
- target journal for publication
- academic/school year
- research agenda alignment
- continuation of previous scholarly work, if applicable

## Co-Authors
For each co-author:
- name
- HAU unit or external institutional affiliation
- mobile number
- email
- percentage of contribution

The system must validate configured minimum contribution rules where applicable.

## Declarations
- data privacy consent
- originality/novelty declaration
- department research agenda alignment
- HAU research agenda alignment
- non-graduate-requirement declaration
- no-similar-graduate-work declaration
- external funding declaration/status

The system must store consent/declaration timestamps and the submitting user.

## Logistical Support
- particular/item
- proposed amount
- approved amount
- remarks
- decision/status
- total proposed
- total approved

## Research Timeline / Gantt Data
- activity
- target start
- target end
- actual start
- actual end
- status
- remarks

---

# 8. Document Management and Versioning

## 8.1 Document Types

At minimum:
- Research Proposal
- Revised Research Proposal
- Turnitin Result
- Evaluation Form
- Consolidated Recommendations
- IRB Document
- Implementation Evidence
- Final Paper
- Revised Final Paper
- Final Turnitin Result
- Presentation/Publication Supporting Document
- Other URO Requirement

## 8.2 Version Rules

Each document version must record:
- document ID
- research ID
- document type
- version number
- original filename
- stored filename/key
- MIME type
- file size
- uploaded by
- uploaded at
- workflow stage
- reason for new version
- checksum/hash
- active/current version flag

Never overwrite a prior version.

## 8.3 Storage

Files must be stored outside the application container's ephemeral filesystem.

Supported v1 approach:
- mounted persistent Docker volume; OR
- S3-compatible object storage (recommended for production, e.g. MinIO)

The database stores metadata and object/storage references, not raw file blobs unless explicitly configured.

---

# 9. Evaluation Model

Evaluation definitions must be configurable because the workflow identifies pass/fail outcomes but does not by itself define all numeric scoring thresholds.

Entities:

- Evaluation Assignment
- Evaluation Round
- Evaluation Submission
- Evaluation Criterion
- Evaluation Result
- Re-evaluation Link

Every evaluation submission must identify the exact document version reviewed.

## Required assignment statuses

- Pending Invitation
- Accepted
- Declined
- In Review
- Submitted
- Re-evaluation Required
- Superseded
- Cancelled

## Required result data

- pass/fail
- numeric score/rating, optional/configurable
- comments
- recommendation
- submitted timestamp
- evaluator identity internally
- blind display identity where appropriate

---

# 10. Turnitin Tracking

Proposal and final-paper Turnitin processes must use the same generalized attempt model.

Fields:
- attempt ID
- research ID
- document version ID
- stage: PROPOSAL or FINAL_PAPER
- similarity/net result
- configured threshold at time of decision
- result: ACCEPTABLE / REVISION_REQUIRED
- report file
- annotations/remarks
- recorded by
- recorded at

The system must retain all attempts.

A later change to the configured similarity threshold must not retroactively alter the recorded decision of an older attempt.

---

# 11. Researcher Dashboard

The researcher dashboard must show:

- My Research
- New Submission
- Action Required
- Under Review
- Approved / In Progress
- Completed
- Notifications

Each research card/row should show:
- title
- tracking number
- current stage/status
- submission date
- current owner/responsible office or generic role
- days in current stage
- deadline
- overdue indicator
- required next action
- progress indicator

The researcher must never need to infer whether action is required.

Example action messages:
- No action required — under external evaluation.
- Revision required — upload revised proposal.
- Final paper Turnitin revision required.
- Final evaluation revision required.
- Research completed — ready for presentation/publication processing.

---

# 12. URO Dashboard

The URO dashboard must provide counts and drill-downs for at least:

- New submissions
- Awaiting Dean Endorsement
- Initial Evaluation
- Proposal Turnitin
- Proposal Turnitin Revision
- External Evaluation
- Selective External Re-evaluation
- IRB Review
- Proposal Approved
- Research In Progress
- Final Paper Due
- Final Paper Turnitin
- Final Paper Turnitin Revision
- Final Blind Evaluation
- Selective Final Re-evaluation
- Completed
- Overdue

Filters:
- school/college/unit
- department
- researcher
- research type
- academic year
- status
- date submitted
- evaluator
- overdue
- target journal
- completion/readiness flags

---

# 13. Timeline / Audit Trail UI

Every research record must show a chronological timeline.

Example:

- Proposal created
- Submitted
- Dean endorsed
- URO received
- Initial evaluation started
- Initial revision requested
- Proposal v2 submitted
- Initial evaluation passed
- Proposal Turnitin attempt 1 recorded
- Proposal revision requested
- Proposal v3 submitted
- Proposal Turnitin passed
- External evaluators assigned
- Evaluator 1 passed
- Evaluator 2 failed
- Revision requested
- Proposal v4 submitted
- Selective re-evaluation assigned to Evaluator 2
- Evaluator 2 passed
- Endorsed to IRB
- IRB approved
- Research implementation started
- Final paper submitted
- Final Turnitin attempt recorded
- Final Turnitin passed
- Blind evaluators assigned
- Final Evaluator 1 passed
- Final Evaluator 2 failed
- Final-paper revision requested
- Final paper v2 submitted
- Selective final re-evaluation assigned to Final Evaluator 2
- Final Evaluator 2 passed
- Final blind evaluation passed
- Research tagged Completed
- Ready for Publication

---

# 14. Notifications and Deadlines

## Notification Channels

Required v1:
- in-app notifications

Recommended/configurable:
- email notifications

## Trigger Examples

- submission received
- endorsement required
- submission returned
- initial evaluation revision required
- Turnitin revision required
- evaluator invitation
- evaluator replacement required
- evaluator deadline approaching
- external evaluation completed
- selective re-evaluation assigned
- IRB revision required
- proposal approved
- milestone due
- final paper due
- final Turnitin revision required
- final blind evaluation assignment
- selective final re-evaluation assignment
- research completed
- presentation/publication ready

## SLA

The system must support configurable stage deadlines/SLA values.

Do not hard-code “10 days” globally; configure per workflow stage so URO can change policy without code changes.

Required fields:
- assigned_at
- due_at
- completed_at
- overdue boolean/derived state
- reminders sent

---

# 15. Search and Reporting

Global URO search must support:
- tracking number
- proposal title
- researcher
- co-author
- evaluator
- school/college/unit
- department
- status
- academic year

Reports:
- submissions by period
- submissions by unit
- current workflow distribution
- average time per stage
- overdue cases
- evaluator workload
- evaluator turnaround
- revision frequency
- Turnitin attempt counts
- research in progress
- completed research
- presentation-ready
- publication-ready

Export:
- CSV for tabular reports
- PDF for selected management reports (later if not part of first sprint)

---

# 16. Administrative Configuration

Admin-configurable reference data:

- schools/colleges
- departments/units
- research categories
- academic years
- research agenda values
- user roles
- evaluator pools
- IRB users
- proposal Turnitin threshold
- final-paper Turnitin threshold
- evaluation scoring schema
- pass/fail policy
- stage SLA days
- notification templates
- file upload size/type limits
- blind-evaluation settings

Configuration changes must be audited.

---

# 17. Functional Requirements

## FR-001 Authentication
The system shall require authentication for all non-public functions.

## FR-002 RBAC
The system shall enforce server-side role and object-level authorization.

## FR-003 Research creation
A Researcher shall be able to create and save a draft.

## FR-004 Submission validation
The system shall prevent submission until mandatory fields/documents/declarations are complete.

## FR-005 Endorsement
The system shall route a submitted research record to the correct Dean/Head based on organizational affiliation.

## FR-006 Initial evaluation
Authorized URO users shall record initial evaluation outcome and comments.

## FR-007 Versioned revisions
Each revision shall create a new immutable document version.

## FR-008 Proposal Turnitin
The system shall record proposal Turnitin attempts and enforce an accepted result before external evaluation.

## FR-009 Evaluator assignment
URO shall assign two proposal evaluators by default.

## FR-010 Invitation workflow
Evaluators shall accept or decline assignments.

## FR-011 Replacement evaluator
URO shall replace a declined evaluator without losing assignment history.

## FR-012 Evaluations
Each evaluator shall submit an independent evaluation tied to a document version.

## FR-013 Selective proposal re-evaluation
The system shall assign revised proposals only to failed evaluator(s) when selective re-evaluation applies.

## FR-014 IRB workflow
The system shall record IRB revision/not-approved/approved outcomes.

## FR-015 Implementation monitoring
Approved research shall support milestone/progress tracking.

## FR-016 Final paper
Researchers shall submit a versioned final paper.

## FR-017 Final-paper Turnitin
The system shall require final-paper Turnitin acceptance before final blind evaluation.

## FR-018 Blind final evaluation
The system shall provide blind evaluator access to the appropriate final-paper package.

## FR-019 Selective final re-evaluation
If one final evaluator fails the paper, only that evaluator shall be reassigned after revision; if multiple fail, all failed evaluators shall be reassigned.

## FR-020 Completion
The system shall prevent `COMPLETED` unless all required final evaluator outcomes are passing and final-paper Turnitin is accepted.

## FR-021 Readiness
Authorized URO users shall independently set Ready for Presentation and Ready for Publication after completion.

## FR-022 Audit
All material workflow actions shall be auditable.

## FR-023 Notifications
The system shall generate in-app notifications for workflow actions requiring attention.

## FR-024 Dashboard
The system shall provide role-specific dashboards.

## FR-025 Reporting
URO shall be able to search/filter/export research records.

---

# 18. Non-Functional Requirements

## NFR-001 Security
- password hashing using a modern algorithm
- secure session/JWT handling
- CSRF protection where applicable
- server-side authorization
- input validation
- output encoding
- rate limiting for authentication
- no secrets committed to source control

## NFR-002 Data Privacy
Researcher personal data and research documents are confidential. Access must be least-privilege.

## NFR-003 Auditability
Workflow history must be append-only from normal application interfaces.

## NFR-004 Reliability
A container restart must not lose database records or uploaded files.

## NFR-005 Backup
Persistent database and document storage must be backup-ready using documented procedures.

## NFR-006 Performance
Typical dashboard/list API requests should target < 2 seconds under normal institutional load.

## NFR-007 Accessibility
UI must use semantic controls, keyboard-accessible actions, sufficient contrast, clear labels, and visible focus states.

## NFR-008 Responsive Web UI
Desktop is primary, but key researcher and evaluator functions must work on tablets and mobile browsers.

## NFR-009 Observability
Services must produce structured logs and expose health checks.

## NFR-010 Timezone
Store timestamps in UTC. Display using the configured institutional timezone, default `Asia/Manila`.

---

# 19. Recommended Technical Architecture

The AI harness should use the following reference architecture unless the repository already establishes equivalent technologies.

## Frontend
- React
- TypeScript
- Vite or Next.js
- component-based UI
- responsive layout

## Backend
- Python FastAPI
- SQLAlchemy
- Alembic migrations
- Pydantic validation
- REST API

## Database
- PostgreSQL 16+ recommended

## Async / Notifications
- Redis recommended
- background worker optional in early MVP but architecture should allow it

## Document Storage
Development:
- Docker persistent volume

Production-ready option:
- MinIO / S3-compatible object storage

## Reverse Proxy
- Nginx or Traefik

The harness may retain an existing equivalent stack if this project already has one; it must not rewrite a working codebase solely to match this recommendation.

---

# 20. Docker Requirements

The complete application must run using Docker Compose.

Minimum logical services:

```yaml
services:
  frontend:
  api:
  db:
```

Recommended production composition:

```yaml
services:
  reverse-proxy:
  frontend:
  api:
  worker:
  redis:
  db:
  object-storage:
```

## Required Docker Behavior

1. `docker compose up -d` must start the application.
2. All application configuration must come from environment variables or mounted configuration.
3. Secrets must use `.env` locally and must not be committed.
4. Database data must use a named persistent volume.
5. Uploaded documents must use a named persistent volume or object storage.
6. Services must define health checks.
7. API startup must wait/retry for database readiness.
8. Database migrations must have a documented execution path.
9. Containers must restart safely.
10. Dockerfiles must use non-root runtime users where practical.
11. Production images should use multi-stage builds where appropriate.
12. Provide `.env.example`.
13. Provide `docker-compose.yml`.
14. Provide a documented backup/restore procedure.
15. Do not store critical state only inside writable container layers.

Suggested ports for local development may be configured through environment variables; do not hard-code production host ports.

---

# 21. Core Data Model

The implementation should include at least the following entities.

## Identity / Organization
- User
- Role
- UserRole
- SchoolCollege
- DepartmentUnit
- UserAffiliation

## Research
- Research
- ResearchAuthor
- ResearchDeclaration
- ResearchStatusHistory
- ResearchReadiness
- ResearchMilestone
- LogisticalSupportRequest
- LogisticalSupportItem

## Documents
- ResearchDocument
- ResearchDocumentVersion

## Workflow
- WorkflowInstance
- WorkflowAction
- WorkflowDeadline

## Turnitin
- SimilarityCheckAttempt

## Evaluation
- EvaluatorProfile
- EvaluationAssignment
- EvaluationRound
- EvaluationSubmission
- EvaluationCriterion / Rubric
- ConsolidatedRecommendation

## IRB
- IRBReview
- IRBDecision

## Notifications
- Notification
- NotificationDelivery

## Audit
- AuditEvent

Foreign keys and constraints must enforce the relationship between an evaluation and the exact document version evaluated.

---

# 22. State Transition Guard Examples

The API must enforce transition guards.

Examples:

### Cannot enter External Evaluation
Unless:
- initial evaluation passed; and
- latest proposal Turnitin attempt is ACCEPTABLE.

### Cannot enter IRB
Unless:
- all currently required external evaluator outcomes are passing.

### Cannot enter Final Blind Evaluation
Unless:
- a Final Paper document exists; and
- latest final-paper Turnitin attempt is ACCEPTABLE.

### Cannot enter Completed
Unless:
- final blind evaluation round is satisfied; and
- all required final evaluator outcomes are passing; and
- final-paper Turnitin remains passed for the evaluated version.

### Selective re-evaluation
When evaluator A passed and evaluator B failed:
- new revision creates an assignment for evaluator B only;
- A's prior passing outcome remains part of the active decision set;
- the new evaluation must be tied to the new revision.

---

# 23. API Surface — Minimum

Exact paths may differ, but equivalent functionality is required.

## Authentication
- POST `/auth/login`
- POST `/auth/logout`
- GET `/auth/me`

## Research
- GET `/research`
- POST `/research`
- GET `/research/{id}`
- PATCH `/research/{id}`
- POST `/research/{id}/submit`

## Documents
- GET `/research/{id}/documents`
- POST `/research/{id}/documents`
- GET `/documents/{id}/versions`
- POST `/documents/{id}/versions`

## Workflow
- GET `/research/{id}/timeline`
- GET `/research/{id}/workflow`
- POST `/research/{id}/actions/{action}`

## Turnitin
- GET `/research/{id}/similarity-checks`
- POST `/research/{id}/similarity-checks`

## Evaluations
- POST `/research/{id}/evaluation-assignments`
- POST `/evaluation-assignments/{id}/accept`
- POST `/evaluation-assignments/{id}/decline`
- POST `/evaluation-assignments/{id}/submit`
- POST `/research/{id}/re-evaluation`

## IRB
- POST `/research/{id}/irb/review`

## Implementation
- GET `/research/{id}/milestones`
- POST `/research/{id}/milestones`
- PATCH `/milestones/{id}`

## Admin
- CRUD reference data and settings as authorized.

---

# 24. UI / Navigation Requirements

## Researcher Navigation
- Dashboard
- My Research
- New Submission
- Action Required
- Notifications
- Profile

## URO Navigation
- Dashboard
- Research Submissions
- Initial Evaluation
- Turnitin
- External Evaluations
- IRB
- Implementation Monitoring
- Final Paper Review
- Reports
- Evaluators
- Administration (if authorized)

## Evaluator Navigation
- Dashboard
- Invitations
- Active Reviews
- Submitted Reviews

## Research Detail Tabs
- Overview
- Workflow
- Documents
- Reviews
- Turnitin
- IRB
- Implementation
- Logistical Support
- Timeline / Audit

Role permissions determine visibility.

---

# 25. Error Handling

The UI must not expose raw backend errors.

Use:
- inline field validation for forms
- modal/toast messages for operation errors
- actionable messages

Examples:
- “A final blind evaluation cannot start until the final paper passes Turnitin.”
- “Only evaluators with a failing result are eligible for this selective re-evaluation.”
- “This document version has already been evaluated.”
- “You do not have permission to perform this action.”

The API must return structured errors with:
- code
- message
- field errors if applicable
- correlation/request ID if logging supports it

---

# 26. Test Requirements

The AI harness must create automated tests for critical workflow rules before declaring implementation complete.

Minimum test cases:

1. Researcher can create draft.
2. Researcher cannot bypass Dean endorsement.
3. Initial revision creates a new version.
4. External evaluation cannot start before proposal Turnitin passes.
5. Proposal Turnitin revision loop works.
6. Declined evaluator can be replaced.
7. Each evaluator result is independent.
8. One failing proposal evaluator causes selective re-evaluation only for that evaluator.
9. Both failing proposal evaluators cause both to be reassigned.
10. IRB approval starts implementation but does not complete research.
11. Final paper can be submitted after implementation stage permits it.
12. Final blind evaluation cannot start before final-paper Turnitin passes.
13. Final-paper Turnitin revision loop works.
14. One failing final evaluator causes selective re-evaluation only for that evaluator.
15. Both failing final evaluators cause both to be reassigned.
16. Passing evaluator's prior result remains valid during selective re-evaluation.
17. Completed cannot be set before final blind evaluation passes.
18. Completed is set after all required final outcomes pass.
19. Presentation and publication readiness can be set independently.
20. Audit trail records all transitions.
21. Unauthorized roles cannot perform privileged actions.
22. Container restart does not lose DB or document state.

---

# 27. Seed / Demo Data

Development seed data should provide:

- 1 System Administrator
- 1 URO Director
- 2 URO Staff
- 2 Dean/Head users
- 3 Researchers
- 4 External Evaluators
- 2 IRB users
- 4 Final Blind Evaluators
- sample schools/departments
- at least one sample research record in each major phase

Never use real production passwords or personal data in seed files.

---

# 28. AI Harness Implementation Rules

The AI harness must follow these rules:

1. Read this PRD before modifying the codebase.
2. Inspect the existing repository before selecting or changing architecture.
3. Preserve working features unless they conflict with this PRD.
4. Do not invent workflow stages not defined here without documenting the reason.
5. Do not remove audit/version history to simplify implementation.
6. Never implement direct arbitrary status editing.
7. Implement backend authorization, not UI-only permissions.
8. Implement database constraints where practical.
9. Use migrations for schema changes.
10. Keep Docker development environment working after each major change.
11. Add/update tests for every workflow change.
12. Never mark a feature complete without running relevant tests.
13. Do not hard-code policy values that are identified as configurable.
14. Keep proposal evaluation and final-paper evaluation distinct.
15. Keep proposal Turnitin and final-paper Turnitin attempts distinct.
16. Preserve individual evaluator outcomes.
17. Preserve selective re-evaluation logic.
18. Ensure Final Paper Turnitin precedes Final Blind Evaluation.
19. Ensure `COMPLETED` is impossible before final blind evaluation passes.
20. Update README/setup documentation with every deployment-impacting change.

---

# 29. Suggested Implementation Phases

## Phase 1 — Foundation
- Docker Compose
- database
- authentication
- RBAC
- organizational data
- base application shell
- migrations
- health checks

## Phase 2 — Submission
- research application
- co-authors
- declarations
- document storage/versioning
- researcher dashboard
- Dean endorsement

## Phase 3 — Initial Review and Proposal Turnitin
- URO receipt
- initial evaluation
- revision cycle
- Turnitin attempts
- threshold configuration

## Phase 4 — External Evaluation
- evaluator pool
- invitations
- replacement
- independent evaluations
- consolidated recommendations
- selective re-evaluation

## Phase 5 — IRB
- IRB routing
- decisions
- revisions
- proposal approval

## Phase 6 — Implementation Monitoring
- milestones
- Gantt/timeline data
- implementation documents
- logistical support monitoring

## Phase 7 — Final Paper
- final paper submission
- final-paper Turnitin
- revision loop

## Phase 8 — Final Blind Evaluation
- blind package
- evaluator assignments
- independent outcomes
- selective final re-evaluation
- completion guard

## Phase 9 — Completion / Reporting
- Completed
- presentation readiness
- publication readiness
- archive
- management reports

## Phase 10 — Hardening
- security review
- permissions review
- audit verification
- backup/restore test
- Docker production configuration
- performance checks
- user acceptance test fixtures

---

# 30. Definition of Done

The product is not considered functionally complete until:

- the full workflow can be executed end to end;
- proposal and final-paper files are versioned;
- proposal Turnitin gates external evaluation;
- final-paper Turnitin gates final blind evaluation;
- selective proposal re-evaluation works;
- selective final re-evaluation works;
- passing evaluator outcomes are preserved appropriately;
- IRB approval does not mark Completed;
- final paper submission does not mark Completed;
- final blind evaluation passing is required for Completed;
- presentation/publication readiness is available after completion;
- all status transitions are audited;
- RBAC is enforced server-side;
- critical workflow tests pass;
- `docker compose up -d` starts a usable environment;
- persistent data survives container restart/recreation;
- setup, migration, backup, and restore instructions are documented.

---

# 31. Acceptance Scenario — Full Happy Path

1. Researcher creates a draft.
2. Researcher completes required application information and uploads proposal v1.
3. Researcher submits.
4. Dean endorses.
5. URO performs initial evaluation and passes it.
6. URO records acceptable proposal Turnitin result.
7. URO assigns two external evaluators.
8. Both accept.
9. Both pass the proposal.
10. URO endorses to IRB.
11. IRB approves.
12. Research implementation begins.
13. Researcher records milestones until research work is done.
14. Researcher submits Final Paper v1.
15. URO records acceptable final-paper Turnitin result.
16. URO assigns blind final evaluators.
17. All required final evaluator outcomes pass.
18. System transitions to Final Blind Evaluation Passed.
19. Authorized action tags research Completed.
20. URO may mark Ready for Presentation and/or Ready for Publication.
21. Record may later be archived.

---

# 32. Acceptance Scenario — Selective Final Re-evaluation

1. Final Paper v1 passes final-paper Turnitin.
2. Blind Evaluator A passes Final Paper v1.
3. Blind Evaluator B fails Final Paper v1.
4. System must not mark the research Completed.
5. URO sends consolidated recommendations.
6. Researcher submits Final Paper v2.
7. If URO policy requires a new Turnitin check for every revised final-paper version, Final Paper v2 must pass Turnitin before re-evaluation. This behavior should be configurable, with the safe default set to **required**.
8. System keeps Evaluator A's passing outcome.
9. System creates a selective re-evaluation assignment for Evaluator B only.
10. Evaluator B reviews the permitted revised version.
11. Evaluator B passes.
12. System determines all required evaluator outcomes are now passing.
13. Final Blind Evaluation is marked Passed.
14. Research is eligible for Completed.
15. Prior v1 results, v2 result, assignments, comments, and timestamps remain visible in the audit history.

---

# 33. Open Policy Settings to Confirm During UAT

The workflow supports these values, but they should remain configurable until URO finalizes policy:

- exact proposal Turnitin threshold
- exact final-paper Turnitin threshold
- whether every revised final paper must undergo Turnitin again before selective re-evaluation
- numeric scoring/rubric and pass threshold
- number of external evaluators
- number of final blind evaluators
- SLA days per stage
- IRB revision routing policy
- evaluator anonymity rules
- publication/presentation completion metadata

The AI harness must implement these as settings or isolated policy constants, not scattered hard-coded conditions.

---

# 34. Final Product Principle

The application must treat the research record as a monitored, auditable lifecycle rather than a collection of uploaded files.

**Documents support the workflow; the workflow controls the research state.**

The application succeeds when authorized users can reliably determine the current stage, responsible party, required action, elapsed time, document version, evaluation history, and final eligibility for completion for every research submission.
