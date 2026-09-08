# Implementation Notes

## Architecture Decisions

### 1. Tech Stack Selection
- **Repository was empty** — no existing code to preserve
- Used PRD-recommended architecture: React + TypeScript + Vite + Tailwind CSS frontend, Python FastAPI + SQLAlchemy + Alembic backend, PostgreSQL database
- Added shadcn/ui-compatible design system per UI spec, but using Tailwind utilities directly for faster iteration

### 2. Database Enum Types
- Used Python enums + SQLAlchemy `Enum` type for `ResearchStatus`, `AssignmentStatus`, `TurnitinStage`, `TurnitinResult`, `IRBDecision`, `MilestoneStatus`
- All status values are defined as enums, not arbitrary strings (WF-001)

### 3. Status History as Audit Trail
- `ResearchStatusHistory` model records every status transition immutably (WF-002)
- Stores: research_id, prior_status, new_status, action, actor_id, actor_role, document_version_id, remarks, timestamp

### 4. Document Versioning
- Separate `ResearchDocument` (document type container) and `ResearchDocumentVersion` (actual version records)
- Never overwrite — always create new version (WF-003, PRD §8.2)
- Each version tracks: version_number, original_filename, stored_filename, mime_type, file_size, checksum, workflow_stage, reason

### 5. Evaluation Model
- Distinguished `EvaluationType.PROPOSAL` and `EvaluationType.FINAL` for separate tracking
- Individual evaluator outcomes stored per assignment, not as aggregate (WF-008)
- Supports selective re-evaluation by tracking round_number and status

### 6. Turnitin Model
- `SimilarityCheckAttempt` supports both PROPOSAL and FINAL_PAPER stages (PRD §10)
- Records threshold_at_decision to prevent retroactive changes (PRD §10)
- All attempts retained

### 7. Configurable Settings
- `SystemSetting` table stores key-value pairs for configurable thresholds
- Not hard-coded — follows PRD §16 and §33

### 8. Seed Data
- 19 demo users across all 8 roles
- 8 schools/colleges matching HAU structure
- Demo passwords are for development only

### 9. Docker Setup
- Multi-stage builds for frontend (node:20-alpine build → nginx:alpine)
- Multi-stage builds for backend (python:3.12-slim with build deps → slim runtime)
- Non-root user in backend container
- Health checks on all services
- Named volumes for PostgreSQL and uploads

### 10. Frontend Design System
- Matches UI Design Spec §3 (Color System) exactly
- Uses Playfair Display for headings, Inter for body text
- Maroon sidebar with gradient per spec
- HAU circular seal logo placed in sidebar
- Motto "VIRTUS · SCIENTIA · CARITAS" at sidebar bottom

## Known Limitations (Phase 1)

1. **No workflow engine yet** — status transitions are not enforced (Phase 6)
2. **No RBAC enforcement** — auth exists but role checks not applied to endpoints yet (Phase 2)
3. **No file upload endpoint** — storage volume configured but no upload API yet (Phase 5)
4. **Frontend pages are static** — not connected to backend API yet
5. **No tests yet** — will be added with each phase

## Conflicts / Resolutions

No material conflicts found between PRD and UI Design Spec at this phase. The UI spec provides visual guidance that aligns with the PRD workflow requirements.
