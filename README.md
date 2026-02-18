# EdgeChat Backend

Backend API for a mobile AI chat app: authentication, conversations with AI (Google Gemini), and usage tracking. Built with FastAPI, PostgreSQL, MongoDB, and Redis.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile Clients                           │
│                    (Android / iOS / Web)                         │
└──────────────────────────┬──────────────────────────────────────┘
                            │  HTTPS + JWT
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────────────┐    │
│  │ Auth API │ │ Chat API │ │   AI API   │ │  Usage API     │    │
│  │ /auth/*  │ │ /chat/*  │ │ /ai/*      │ │  /usage/*      │    │
│  └──────────┘ └──────────┘ └────────────┘ └────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Request ID │ Rate Limit │ Usage Log │ CORS              │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────────┐
│ PostgreSQL │ │  MongoDB   │ │  Redis   │ │  Google Gemini  │
│ Users      │ │  Chat      │ │  Rate    │ │  Chat / Complete │
│ API usage  │ │  history   │ │  limits  │ │                 │
└────────────┘ └────────────┘ └──────────┘ └─────────────────┘
```

---

## Tech Stack

| Layer        | Choice        | Rationale |
|-------------|---------------|-----------|
| **API**     | FastAPI       | Async I/O for slow AI calls; auto OpenAPI docs; Pydantic validation. |
| **Auth**    | JWT (access + refresh) | Stateless; no server sessions; mobile-friendly. |
| **SQL**     | PostgreSQL + SQLAlchemy (async) | Users, auth, usage logs; ACID. |
| **NoSQL**   | MongoDB (Motor) | Chat history; flexible schema for messages. |
| **Cache / limits** | Redis | Rate limiting; future response cache. |
| **AI**      | Google Gemini (google-genai) | Chat and completion. |

---

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16, MongoDB 7, Redis 7 (or use Docker)

### Local (without Docker)

1. Clone and create a virtualenv:
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # source venv/bin/activate  # Linux/macOS
   pip install -r requirements.txt
   ```

2. Copy environment file and set variables:
   ```bash
   copy .env.example .env   # Windows
   # cp .env.example .env   # Linux/macOS
   ```
   Edit `.env`: set `DATABASE_URL`, `MONGODB_URL`, `REDIS_URL`, `JWT_SECRET`, and optionally `GEMINI_API_KEY`.

3. Run PostgreSQL, MongoDB, and Redis locally (or via Docker for only the databases).

4. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```
   - API: http://localhost:8000  
   - Swagger UI: http://localhost:8000/docs  

### Docker (full stack)

```bash
docker-compose up --build
```

API and docs are at http://localhost:8000 and http://localhost:8000/docs. The app uses the DBs and Redis from the Compose stack.

---

## API Overview

| Area   | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| **Auth** | POST | `/api/v1/auth/register` | Register; returns tokens. |
|        | POST | `/api/v1/auth/login` | Login; returns tokens. |
|        | POST | `/api/v1/auth/refresh` | Refresh access token. |
|        | GET  | `/api/v1/auth/me` | Current user (Bearer). |
| **AI**  | POST | `/api/v1/ai/complete` | One-off Gemini completion. |
| **Chat**| POST | `/api/v1/chat/conversations` | Create conversation. |
|        | GET  | `/api/v1/chat/conversations` | List conversations (paginated). |
|        | POST | `/api/v1/chat/conversations/{id}/messages` | Send message; get AI reply. |
|        | GET  | `/api/v1/chat/conversations/{id}/messages` | Message history (paginated). |
|        | DELETE | `/api/v1/chat/conversations/{id}` | Delete conversation. |
| **Usage** | GET | `/api/v1/usage/me` | Current user usage stats (Bearer). |
| **Health** | GET | `/api/v1/health` | Liveness. |
|        | GET | `/api/v1/health/ready` | Readiness (DB, Mongo, Redis). |
|        | GET | `/api/v1/health/db` | PostgreSQL check. |
|        | GET | `/api/v1/health/mongo` | MongoDB check. |

**API documentation (Swagger):** http://localhost:8000/docs  

**Authentication:** `Authorization: Bearer <access_token>` for protected routes.

---

## Design Decisions

- **Stateless app + JWT:** No server-side sessions; any instance can serve any request. Enables horizontal scaling behind a load balancer.
- **PostgreSQL for users and usage:** Structured, ACID; good for auth and analytics.
- **MongoDB for chat history:** Flexible document shape for messages and AI replies.
- **Redis:** Rate limiting per IP; ready for response caching (e.g. idempotency or AI cache).
- **Structured errors:** All errors return JSON with `detail` and optional `request_id` for support.
- **Health:** `/health` for liveness; `/health/ready` for readiness (all dependencies). Use in Kubernetes or load balancers.

For more system-design context (scaling, mobile API, caching, security, observability), see [DAY6_SYSTEM_DESIGN.md](DAY6_SYSTEM_DESIGN.md).

---

## Tests

```bash
pytest
```

Uses `.env.test` if present; see `tests/conftest.py` for fixtures and test DB.

---

## License

MIT (or your choice).
