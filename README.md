# URO Research Monitoring System

A workflow-driven web application for monitoring research submissions through the University Research Office (URO) review lifecycle at Holy Angel University.

## Quick Start (Docker)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Build and start services
docker compose up -d --build

# 3. Run database migrations
docker compose exec api alembic upgrade head

# 4. Seed development data
docker compose exec api python -m seed

# 5. Access the application
# Frontend: http://localhost:5173
# API:      http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| System Administrator | admin@hau.edu.ph | admin123 |
| URO Director | uro.director@hau.edu.ph | director123 |
| URO Staff | uro.staff1@hau.edu.ph | staff123 |
| Dean (SOC) | dean.soc@hau.edu.ph | dean123 |
| Researcher | researcher1@hau.edu.ph | researcher123 |
| External Evaluator | evaluator1@hau.edu.ph | evaluator123 |
| IRB Reviewer | irb1@hau.edu.ph | irb123 |
| Final Evaluator | final1@hau.edu.ph | final123 |

## Architecture

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16
- **Containerization**: Docker Compose

## Development

### Frontend (standalone)
```bash
cd frontend
npm install
npm run dev
```

### Backend (standalone)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Database Migrations
```bash
# Create migration after model changes
docker compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback
docker compose exec api alembic downgrade -1
```

## Backup & Restore

### Backup Database
```bash
docker compose exec db pg_dump -U uro_user uro_research > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
cat backup.sql | docker compose exec -T db psql -U uro_user -d uro_research
```

### Backup Uploads
```bash
docker compose exec api tar czf /tmp/uploads_backup.tar.gz -C /data uploads
docker compose cp api:/tmp/uploads_backup.tar.gz ./uploads_backup.tar.gz
```

## Project Structure

```
.
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── security/     # Auth, JWT, RBAC
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   ├── tests/            # Backend tests
│   └── Dockerfile
├── frontend/             # React SPA
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   └── assets/       # Static assets
│   └── Dockerfile
├── docs/                 # Documentation & assets
│   ├── IMPLEMENTATION_PLAN.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── *.png             # Design assets
├── docker-compose.yml
├── .env.example
└── README.md
```

## License

Internal use only — Holy Angel University.
