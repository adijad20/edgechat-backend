# Day 5 — Testing + Docker + CI/CD

## Done

- **Testing**: pytest + pytest-asyncio + httpx; fixtures in `tests/conftest.py` (client, auth_headers, mock_gemini_*).
- **Unit tests**: `tests/test_security.py` (hash_password, verify_password, create_access_token, decode_token).
- **Integration tests**: `tests/test_auth_api.py` (register, login, me, refresh, usage/me), `tests/test_health.py`, `tests/test_ai_api.py` (mocked Gemini), `tests/test_chat_api.py` (conversations/messages with mocked Gemini).
- **Docker**: `Dockerfile`, `docker-compose.yml` (app + PostgreSQL + MongoDB + Redis), `.dockerignore`.
- **CI**: `.github/workflows/ci.yml` — lint (ruff), test (pytest with service containers), Docker build.

---

## Detailed steps to verify Day 5

**Do I need to enable venv?**  
**Yes**, for running tests and lint locally. Use the project’s venv so `pytest` and `ruff` use the same Python and dependencies as the app. For “full stack” with `docker-compose up` you don’t need venv (the app runs inside Docker).

---

### Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose) installed and running — needed for Postgres/Mongo/Redis (and for full stack).
- **Python 3.11** — the one used to create `venv`.

---

### Part A: Run tests locally (pytest)

Tests talk to PostgreSQL, MongoDB, and Redis on **localhost** (same URLs as in `tests/conftest.py`). Start those via Docker, then run pytest **inside your venv**.

1. **Open a terminal** in the project root:  
   `c:\Users\IN009361\Desktop\BackendProjects\smartlens-ai`

2. **Activate the virtual environment**  
   - Windows (PowerShell):  
     `.\venv\Scripts\Activate.ps1`  
   - Windows (CMD):  
     `.\venv\Scripts\activate.bat`  
   - You should see `(venv)` in the prompt.

3. **Start only the databases** (no app container yet):
   ```bash
   docker-compose up -d postgres mongodb redis
   ```
   Wait until all three are “Up”. Check with:  
   `docker-compose ps`

4. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

5. **Run all tests**:
   ```bash
   pytest -v
   ```
   - You should see unit tests (`test_security.py`) and integration tests (`test_auth_api.py`, `test_health.py`, `test_ai_api.py`, `test_chat_api.py`) run and pass.
   - If something fails, check that Postgres, Mongo, and Redis are reachable on `localhost:5432`, `localhost:27017`, `localhost:16379` (Redis uses 16379 on host to avoid Windows reserved ports).

**If you see `InvalidPasswordError` or Mongo/health 503:**  
Tests load your project **`.env`** first (the same file used when you run `uvicorn`), so they use the same `DATABASE_URL`, `MONGODB_URL`, and `REDIS_URL` as the rest of the project. If tests still fail, check that `.env` exists and has the correct URLs and that Postgres/Mongo/Redis are running.

6. **(Optional) Run a single test file**:
   ```bash
   pytest tests/test_security.py -v
   pytest tests/test_auth_api.py -v
   ```

7. **Stop the DB containers** when done:
   ```bash
   docker-compose down
   ```

---

### Part B: Run full stack (app + DBs in Docker)

Here you don’t need to activate venv; everything runs in containers.

1. **In the project root**, start the whole stack:
   ```bash
   docker-compose up --build
   ```
   First time it will build the app image and pull Postgres/Mongo/Redis images.

2. **Wait until you see** something like:  
   `Uvicorn running on http://0.0.0.0:8000`

3. **Verify**:
   - Open browser: **http://localhost:8000** → should return `{"status":"ok","app":"EdgeChat Backend"}`.
   - Open **http://localhost:8000/docs** → Swagger UI should load.
   - Try **POST /api/v1/auth/register** and **POST /api/v1/auth/login** from the docs (or with curl/Postman).

4. **Stop** with `Ctrl+C`, then:
   ```bash
   docker-compose down
   ```

Ensure your `.env` has at least `JWT_SECRET`; optional `GEMINI_API_KEY` for AI endpoints.

---

### Part C: Lint and Docker build (same as CI, locally)

**Use venv** so `ruff` uses the project’s Python.

1. **Activate venv** (same as Part A, step 2).

2. **Install ruff** (not in requirements.txt; CI installs it separately):
   ```bash
   pip install ruff
   ```

3. **Run lint**:
   ```bash
   ruff check .
   ```
   Fix any reported issues if you want a green CI.

4. **Build the Docker image** (no venv needed; Docker uses its own build):
   ```bash
   docker build -t edgechat-backend:local .
   ```
   Build should finish without errors.

---

### Part D: Verify CI on GitHub

1. Push your repo to GitHub (if not already), including the `.github/workflows/ci.yml` and Day 5 code.

2. Go to the repo on GitHub → **Actions** tab.

3. Push a commit to `main` or `master` (or open a PR). The **CI** workflow should run:
   - **lint**: `ruff check .`
   - **test**: pytest with Postgres/Mongo/Redis service containers
   - **docker**: `docker build`

4. All jobs should turn green when tests and lint pass and the image builds.

---

## Quick reference

| What you want to do        | Use venv? | Command / steps |
|----------------------------|-----------|------------------|
| Run pytest locally         | Yes       | Activate venv → `docker-compose up -d postgres mongodb redis` → `pytest -v` |
| Run full app + DBs         | No        | `docker-compose up --build` |
| Run ruff locally            | Yes       | Activate venv → `pip install ruff` → `ruff check .` |
| Build Docker image locally  | No        | `docker build -t edgechat-backend:local .` |
| See CI run                  | —         | Push to `main`/`master` and check GitHub Actions |
