# Gym CRM — SaaS Backend API

A production-grade multi-tenant SaaS CRM backend built with FastAPI and PostgreSQL, designed for gym management. Each gym operates as a fully isolated tenant with its own staff, members, workout sessions, and progress tracking.

> **Live on AWS** — containerized, deployed to ECS Fargate, RDS-backed, with a green CI/CD pipeline on every push to `main`.
>
> Interactive API docs (Swagger UI): `/docs` once running locally → [http://localhost:8000/docs](http://localhost:8000/docs)
>
> _Add a screenshot of the Swagger UI here once you grab one — drop it in `/docs-assets/swagger.png` and reference it._

---

## Motivation

I'm a developer who ships full-stack apps end to end. My flagship product (TrainerOS, aftrainer.app) is a React PWA with a Supabase backend — that taught me a lot about the BaaS world, but I wanted to prove I could build a backend the hard way: from the database schema up, with my own layers, my own auth, my own tests, and my own infrastructure.

So I built this. A real multi-tenant CRM for gym owners — not a tutorial clone, not a localhost demo. Every layer is hand-built and tested: SQLAlchemy models → repository → service → FastAPI routers, with JWT + role-based access for `manager` and `trainer` accounts. It's containerized with Docker, runs on AWS Fargate behind RDS, ships secrets through AWS Secrets Manager, and redeploys automatically when CI goes green.

The goal was simple: a backend I'd be proud to put in front of an engineer who actually reads the code.

---

## Quick Start

The fastest path is Docker Compose — one command, full stack (API + PostgreSQL + Redis):

```bash
git clone https://github.com/Adrianbrou/Saas-CRM-Backend-gym-trainer-
cd Saas-CRM-Backend-gym-trainer-/app
docker-compose up --build
```

Then open:

- **API:** [http://localhost:8000](http://localhost:8000)
- **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

### Without Docker

```bash
# 1. Set up the virtual environment
python -m venv .venv
source .venv/bin/activate     # macOS / Linux
.venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file at the project root
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/crm_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 4. Run migrations and start the server
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

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
| Testing | Pytest (unit + integration, 52 tests) |
| CI/CD | GitHub Actions |
| Cloud | AWS (ECS Fargate, RDS, ECR, Secrets Manager) |

---

## Usage

### Architecture

```text
Client
  └── FastAPI (API layer)
        └── Service layer (business logic)
              └── Repository layer (DB queries)
                    └── PostgreSQL (AWS RDS)
                          + Redis (caching layer)
```

Each layer has one responsibility. No layer skips another. Services raise `ValueError`, routers translate them into proper HTTP status codes.

### Domain Model

```text
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

### Project Structure

```text
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

### Features

- **Multi-tenant architecture** — every query is scoped to `gym_id`, no data leaks between tenants
- **Role-based access control** — `manager` mutates, `trainer` operates, enforced on every protected route
- **JWT authentication** — stateless, OAuth2 password flow, Swagger "Authorize" button works out of the box
- **Redis caching** — `get_by_id` cached with 5min TTL, invalidated on update/delete
- **Background email notifications** — welcome email on member registration, session notification on attendance
- **Paginated list endpoints** — every list route supports `skip` / `limit`
- **Health check endpoint** — `GET /health` returns `200 {"status": "ok"}` for uptime monitoring
- **52 automated tests** — unit per service, integration per API endpoint, all green in CI
- **Seed migration** — 9 body parts seeded via Alembic on first deploy

### API Endpoints

#### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | None | Login, returns JWT |

#### Gyms

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/gyms/` | None | Register a new gym |
| GET | `/gyms/{id}` | Any | Get gym by ID |
| GET | `/gyms/` | Any | List all gyms |
| PATCH | `/gyms/{id}` | Manager | Update gym |
| DELETE | `/gyms/{id}` | Manager | Delete gym |

#### Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/members/` | Manager | Register a member |
| GET | `/members/{id}` | Any | Get member by ID |
| GET | `/members/gyms/{gym_id}` | Any | List gym members |
| PATCH | `/members/{id}` | Manager | Update member |
| DELETE | `/members/{id}` | Manager | Delete member |

#### Staff

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/staff/` | Manager | Add staff member |
| GET | `/staff/{id}` | Any | Get staff by ID |
| GET | `/staff/gym/{gym_id}` | Any | List gym staff |
| PATCH | `/staff/{id}` | Manager | Update staff |
| DELETE | `/staff/{id}` | Manager | Delete staff |

#### Workouts

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/workouts/` | Manager | Create workout |
| GET | `/workouts/{id}` | Any | Get workout by ID |
| GET | `/workouts/` | Any | List all workouts |
| PATCH | `/workouts/{id}` | Manager | Update workout |
| DELETE | `/workouts/{id}` | Manager | Delete workout |

#### Workout Sessions

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/workout-sessions/` | Manager | Create session |
| GET | `/workout-sessions/{id}` | Any | Get session by ID |
| GET | `/workout-sessions/gym/{gym_id}` | Any | List gym sessions |
| POST | `/workout-sessions/{id}/members` | Any | Add member to session |
| DELETE | `/workout-sessions/{id}/members/{member_id}` | Manager | Remove member |

#### Progress

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

#### Health

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |

---

## AWS Deployment

Deployed using:

- **ECR** — Docker image registry
- **ECS Fargate** — serverless container runtime
- **RDS** — managed PostgreSQL
- **Secrets Manager** — secure environment variables
- **GitHub Actions** — CI/CD pipeline (test → deploy on push to `main`)

Pipeline: push to `main` → 52 tests run → if green → Docker image built and pushed to ECR → ECS service redeployed automatically.

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

## Contributing

Want to pull it down and play with it? Here's the quickest path:

### Clone the repo

```bash
git clone https://github.com/Adrianbrou/Saas-CRM-Backend-gym-trainer-
cd Saas-CRM-Backend-gym-trainer-/app
```

### Build the stack

```bash
docker-compose up --build
```

### Run the test suite

```bash
# Make sure Redis is running first (docker-compose handles this)
docker-compose up cache -d

# Run all 52 tests
pytest tests/ -v
```

### Submit a pull request

Fork the repo, branch off `main`, and open a PR with a clear description of what you changed and why. Tests should stay green.

---

## Author

**Adrian Brou**

- GitHub: [@Adrianbrou](https://github.com/Adrianbrou)
- LinkedIn: [linkedin.com/in/adrianbrou](https://linkedin.com/in/adrianbrou)
