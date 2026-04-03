# Gym CRM — SaaS Backend API

A production-grade multi-tenant SaaS CRM backend built with FastAPI and PostgreSQL, designed for gym management. Each gym operates as an isolated tenant with its own staff, members, workout sessions, and progress tracking.

Live API: deployed on AWS ECS Fargate with CI/CD via GitHub Actions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL (AWS RDS) |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT + bcrypt (RBAC) |
| Cache | Redis |
| Containerization | Docker + docker-compose |
| Testing | Pytest (unit + integration) |
| CI/CD | GitHub Actions |
| Cloud | AWS (ECS Fargate, RDS, ECR, Secrets Manager) |

---

## Architecture

```
Client
  └── FastAPI (API layer)
        └── Service layer (business logic)
              └── Repository layer (DB queries)
                    └── PostgreSQL (AWS RDS)
                          + Redis (caching layer)
```

Each layer has one responsibility. No layer skips another.

---

## Domain Model

```
Gym (tenant)
├── Staff (role: manager | trainer)
└── Member
    └── Progress (weight, sets, reps per workout per session)

WorkoutSession
├── Staff (trainer running the session)
├── Members via Attendance (many-to-many)
└── Workouts via SessionWorkouts (many-to-many)

Workout
└── BodyPart (Chest, Back, Legs, Arms, Shoulders, Core, Glutes, Calves, Traps)
```

---

## Project Structure

```
app/
├── app/
│   ├── main.py
│   ├── api/              # FastAPI routers — one file per resource
│   ├── services/         # Business logic — duplicate checks, not-found errors
│   ├── repository/       # Database queries — no business logic
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas (Create, Update, Response)
│   ├── database/         # Engine, session, base
│   └── core/             # Security, JWT, email, logging, cache, dependencies
├── migrations/           # Alembic migration files
├── tests/                # Pytest test suite (unit + integration)
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

---

## Features

- Multi-tenant architecture — each gym is fully isolated
- Role-based access control — manager vs trainer permissions enforced on every route
- JWT authentication — stateless, secure, token-based login
- Redis caching — get_by_id cached with 5min TTL, invalidated on update/delete
- Background email notifications — welcome email on member registration, session notification on attendance
- Paginated list endpoints — all list routes support skip/limit
- Health check endpoint — GET /health for uptime monitoring
- 52 tests passing — unit tests per service + integration tests per API endpoint
- Seed migration — 9 body parts seeded via Alembic on first deploy

---

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | None | Login, returns JWT |

### Gyms
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/gyms/` | None | Register a new gym |
| GET | `/gyms/{id}` | Any | Get gym by ID |
| GET | `/gyms/` | Any | List all gyms |
| PATCH | `/gyms/{id}` | Manager | Update gym |
| DELETE | `/gyms/{id}` | Manager | Delete gym |

### Members
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/members/` | Manager | Register a member |
| GET | `/members/{id}` | Any | Get member by ID |
| GET | `/members/gyms/{gym_id}` | Any | List gym members |
| PATCH | `/members/{id}` | Manager | Update member |
| DELETE | `/members/{id}` | Manager | Delete member |

### Staff
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/staff/` | Manager | Add staff member |
| GET | `/staff/{id}` | Any | Get staff by ID |
| GET | `/staff/gym/{gym_id}` | Any | List gym staff |
| PATCH | `/staff/{id}` | Manager | Update staff |
| DELETE | `/staff/{id}` | Manager | Delete staff |

### Workouts
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/workouts/` | Manager | Create workout |
| GET | `/workouts/{id}` | Any | Get workout by ID |
| GET | `/workouts/` | Any | List all workouts |
| PATCH | `/workouts/{id}` | Manager | Update workout |
| DELETE | `/workouts/{id}` | Manager | Delete workout |

### Workout Sessions
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/workout-sessions/` | Manager | Create session |
| GET | `/workout-sessions/{id}` | Any | Get session by ID |
| GET | `/workout-sessions/gym/{gym_id}` | Any | List gym sessions |
| POST | `/workout-sessions/{id}/members` | Any | Add member to session |
| DELETE | `/workout-sessions/{id}/members/{member_id}` | Manager | Remove member |

### Progress
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/progress/` | Any | Log progress |
| GET | `/progress/{id}` | Any | Get progress by ID |
| GET | `/progress/` | Any | List all progress |
| GET | `/progress/member/{id}` | Any | Progress by member |
| GET | `/progress/workout/{id}` | Any | Progress by workout |
| GET | `/progress/session/{id}` | Any | Progress by session |
| PATCH | `/progress/{id}` | Any | Update progress |
| DELETE | `/progress/{id}` | Any | Delete progress |

### Health
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |

---

## Local Setup

### Requirements
- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Run with Docker
```bash
docker-compose up --build
```

API at: http://localhost:8000
Docs at: http://localhost:8000/docs

### Run locally
```bash
# 1. Clone and activate virtual environment
git clone https://github.com/Adrianbrou/Saas-CRM-Backend-gym-trainer-
cd app
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/crm_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run tests
```bash
# Start Redis first
docker-compose up cache -d

# Run tests
pytest tests/ -v
```

---

## AWS Deployment

Deployed using:
- **ECR** — Docker image registry
- **ECS Fargate** — serverless container runtime
- **RDS** — managed PostgreSQL
- **Secrets Manager** — secure environment variables
- **GitHub Actions** — CI/CD pipeline (test → deploy on push to main)

Pipeline: push to main → 52 tests run → if green → Docker image built and pushed to ECR → ECS service redeployed automatically.

---

## Roadmap

- [x] Phase 1 — Database models + migrations
- [x] Phase 2 — Repository layer
- [x] Phase 3 — Pydantic schemas
- [x] Phase 4 — Service layer
- [x] Phase 5 — API endpoints
- [x] Phase 6 — JWT authentication + RBAC
- [x] Phase 7 — Background tasks + email notifications
- [x] Phase 8 — Redis caching + performance
- [x] Phase 9 — Testing (52 tests — unit + integration)
- [x] Phase 10 — Docker + AWS deployment + CI/CD
- [ ] Phase 11 — Load balancer + custom domain + HTTPS
- [ ] Phase 12 — React frontend

---

## Author

Adrian Brou
LinkedIn: linkedin.com/in/adrianbrou
GitHub: github.com/Adrianbrou
