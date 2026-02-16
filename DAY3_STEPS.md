# Day 3 — EdgeChat Backend: Step-by-Step

Backend for a mobile AI app: auth, chat, vision, summarization. We build it one step at a time like Day 2.

---

## Concepts You'll Meet

| Term | What it is |
|------|------------|
| **pydantic-settings** | Load configuration from environment variables (and `.env`). Validates types and required keys. |
| **JWT** | JSON Web Token — signed token that encodes user identity. Client sends it in `Authorization: Bearer <token>`. Stateless auth. |
| **bcrypt** | Password hashing: we never store plain passwords; we hash and verify. |
| **CORS** | Cross-Origin Resource Sharing — lets a frontend on another origin (e.g. mobile app or different domain) call your API. |
| **Middleware** | Code that runs for every request (before/after the route): logging, request ID, rate limit, etc. |

---

## The Steps (Roadmap)

- **Step 0** — Project skeleton, Docker (Postgres + Mongo + Redis), minimal FastAPI app. ✓ Start here
- **Step 1** — Config from environment (pydantic-settings, `.env`).
- **Step 2** — User model in PostgreSQL + DB session (SQLAlchemy async).
- **Step 3** — Auth: register (hash password), login (return JWT access + refresh).
- **Step 4** — Auth dependency: protect routes, get current user from JWT.
- **Step 5** — Middleware: CORS, request ID, global exception handler.
- **Step 6** — Rate limiting (Redis, per-IP). ✓ You are here

Do **Step 0** and **Step 1** first. When you're comfortable, say "ready for Step 2" and we'll add the next part.

---

## Step 0 — Project skeleton + Docker + minimal app

### What you're learning
- Same idea as Day 2: one `docker compose up -d` to run Postgres, MongoDB, and Redis.
- Project layout: `app/` for the FastAPI application, `main.py` as the entry point. We'll add more modules in later steps.

### What to do

1. **Start the databases** (from `smartlens-ai` folder):
   ```powershell
   cd c:\Users\IN009361\Desktop\BackendProjects\smartlens-ai
   docker compose up -d
   docker compose ps
   ```
   You should see `smartlens-postgres`, `smartlens-mongo`, `smartlens-redis` running.

2. **Create a `.env` file** (required for the app to start — config loads from it):
   ```powershell
   copy env.example .env
   ```
   Edit `.env` and ensure `DATABASE_URL`, `MONGODB_URL`, `REDIS_URL`, `JWT_SECRET` are set (values in `env.example` work with the Docker stack above).

3. **Create virtual environment and install dependencies**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```
   Open http://localhost:8000 — you should see `{"status":"ok"}`.  
   Open http://localhost:8000/docs — Swagger UI loads.

### Verify
- `docker compose ps` shows three containers running.
- `uvicorn app.main:app --reload` starts without error; `/` returns `{"status":"ok"}`; `/docs` works.

### If something fails
- **Port in use** — Another app (e.g. day2-learn) is using 5432/27017/6379. Stop that stack or change ports in `docker-compose.yml`.
- **No module named app** — Run from the `smartlens-ai` folder (where `app/` lives).

---

## Step 1 — Config from environment (pydantic-settings)

### What you're learning
- **Configuration** should come from the environment (or `.env`), not be hardcoded. So we can use different DB URLs and secrets in dev vs prod.
- **pydantic-settings** reads env vars (and optionally a `.env` file), validates them, and gives you a typed `Settings` object. Missing or invalid values fail at startup.

### What to do

1. **Copy the example env file and fill in values**:
   ```powershell
   copy env.example .env
   ```
   (If your editor or OS hides `.env`, create a file named `.env` in `smartlens-ai` with the same content as `env.example`.)
   Edit `.env` and set at least:
   - `DATABASE_URL=postgresql+asyncpg://postgres:secret@localhost:5432/smartlensdb`
   - `MONGODB_URL=mongodb://localhost:27017`
   - `REDIS_URL=redis://localhost:6379`
   - `JWT_SECRET=your-secret-at-least-32-chars-long-change-in-prod`
   - `GEMINI_API_KEY=` (leave empty for now, or add your key from Step 4)

2. **Run the app again**:
   ```powershell
   uvicorn app.main:app --reload
   ```
   Visit http://localhost:8000 — the root route now shows the app name from config (so we know config loaded).

### What the code does
- `app/config.py`: defines `Settings` with required fields (DATABASE_URL, etc.). `BaseSettings` reads from the environment and from `.env` if present.
- `app/main.py`: imports `settings` and uses e.g. `settings.APP_NAME` so you see that config is working.

### Verify
- App starts; root response includes a value from config (e.g. app name). No error about missing env vars.

### If something fails
- **ValidationError** — A required env var is missing or wrong type. Check `.env` and variable names (case-sensitive).

---

## Step 2 — User model + DB session (PostgreSQL, SQLAlchemy async)

### What you're learning
- **User model**: one table `users` with `id`, `email` (unique), `hashed_password`, `created_at`. Same idea as Day 2's `Item` — a Python class maps to a table. We'll store the hashed password in Step 3 (never plain text).
- **dependencies.py**: shared engine and session factory. `get_session()` yields one session per request; commit on success, rollback on error. Routes that need the DB declare `session: SessionDep`.
- **Lifespan**: create all tables (from `Base.metadata`) on startup so `users` exists; dispose the engine on shutdown.
- **Health check**: `GET /api/v1/health/db` uses the session to run `SELECT 1` — proves the DB connection and dependency injection work.

### What to do

1. **Install dependencies** (venv activated):
   ```powershell
   pip install -r requirements.txt
   ```
   This adds `sqlalchemy[asyncio]` and `asyncpg`.

2. **Ensure `.env` has the correct DATABASE_URL** (must use async driver for SQLAlchemy):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:secret@localhost:5432/smartlensdb
   ```
   If you used `postgresql://` (without `+asyncpg`), change it so the app can use the async engine.

3. **Start Postgres and run the app**:
   ```powershell
   docker compose up -d
   uvicorn app.main:app --reload
   ```

4. **Verify**:
   - Open http://localhost:8000/api/v1/health/db — you should see `{"status":"ok","database":"connected"}`. That means the session ran a query against PostgreSQL.
   - The `users` table was created on startup (you can check in a DB client or in Step 3 when we insert a user).

### What the code does

| File | Purpose |
|------|--------|
| `app/models/base.py` | `Base` (DeclarativeBase) — all models inherit from it. |
| `app/models/user.py` | `User` table: id, email (unique), hashed_password, created_at. |
| `app/dependencies.py` | `engine`, `async_session_factory`, `get_session()`, `SessionDep`. Same pattern as Day 2. |
| `app/main.py` | Lifespan: `Base.metadata.create_all`, then dispose. Route `GET /api/v1/health/db` uses `SessionDep` and runs `SELECT 1`. |

### Verify
- `GET /api/v1/health/db` returns 200 and `database: connected`. App starts without DB errors.

### If something fails
- **relation "users" does not exist** — Lifespan should create it; ensure `create_all` runs (no error before it) and that you're connecting to the right DB (same as in docker-compose).
- **Connection refused** — `docker compose up -d`, Postgres running, correct `DATABASE_URL` in `.env`.
- **asyncpg.exceptions.InvalidCatalogNameError** — Database name in URL must match `POSTGRES_DB` in docker-compose (`smartlensdb`).

---

## Step 3 — Auth: register, login, refresh (JWT + bcrypt)

### What you're learning
- **Password hashing**: We never store plain passwords. On register we call `hash_password(plain)` and store the result in `users.hashed_password`. On login we call `verify_password(plain, hashed)` to check. **bcrypt** is used (via passlib).
- **JWT**: After register or login we create two tokens: **access_token** (short-lived, e.g. 15 min) and **refresh_token** (long-lived, e.g. 7 days). The client sends `Authorization: Bearer <access_token>` on API requests. When the access token expires, the client calls **POST /refresh** with the refresh token to get a new pair. Tokens are signed with `JWT_SECRET` so we can verify they weren't tampered with.
- **Routes**: Register (create user, return tokens), Login (verify password, return tokens), Refresh (validate refresh token, return new tokens). All under `/api/v1/auth`.

### What to do

1. **Install dependencies** (venv activated):
   ```powershell
   pip install -r requirements.txt
   ```
   This adds `passlib[bcrypt]`, `python-jose[cryptography]`, and `email-validator`.

2. **Run the app** (Postgres up):
   ```powershell
   uvicorn app.main:app --reload
   ```

3. **Try in Swagger** (http://localhost:8000/docs):
   - **POST /api/v1/auth/register** — body: `{"email": "you@example.com", "password": "secret123"}`. You should get 201 and `access_token`, `refresh_token`, `token_type: "bearer"`.
   - **POST /api/v1/auth/login** — same body. You get the same shape (tokens).
   - **POST /api/v1/auth/refresh** — body: `{"refresh_token": "<paste refresh_token from login>"}`. You get a new access_token and refresh_token.
   - Register again with the same email → 400 "Email already registered". Wrong password on login → 401 "Invalid email or password".

### What the code does

| File | Purpose |
|------|--------|
| `app/core/security.py` | `hash_password`, `verify_password` (bcrypt). `create_access_token`, `create_refresh_token`, `decode_token` (JWT). |
| `app/schemas/auth.py` | Pydantic: RegisterRequest, LoginRequest, RefreshRequest, TokenResponse. EmailStr validates email format. |
| `app/api/v1/auth.py` | Register: check email unique, hash password, create User, return tokens. Login: find user, verify password, return tokens. Refresh: decode refresh token, return new tokens. |
| `app/main.py` | `include_router(auth_router.router, prefix="/api/v1")` so routes are under /api/v1/auth. |

### Verify
- Register returns tokens; login returns tokens; refresh returns new tokens. Duplicate email → 400; wrong password → 401.

### If something fails
- **ImportError: jose** — `pip install python-jose[cryptography]`.
- **ValidationError: email** — Use a valid email format (e.g. `user@example.com`).
- **401 on refresh** — Paste the full refresh_token string (no extra spaces). Token may be expired (default 7 days).

---

## Step 4 — Auth dependency: protect routes, get current user from JWT

### What you're learning
- **Protected route**: A route that requires the client to send a valid **access token** in the `Authorization: Bearer <token>` header. If the token is missing or invalid, we return **401 Unauthorized**.
- **get_current_user dependency**: Extracts the Bearer token from the `Authorization` header (via **HTTPBearer**), decodes the JWT with `decode_token`, checks that it's an **access** token (not refresh), reads the user id from `sub`, loads the **User** from the DB, and returns it. Any route that declares `current_user: CurrentUserDep` will get the authenticated User or 401. We use HTTPBearer (not OAuth2PasswordBearer) so Swagger shows a single "Value" field — you paste only your access_token there.
- **GET /me**: Example protected route — returns the current user's id and email. Used to prove "I'm logged in as this user."

### What to do

1. **Run the app** (no new deps):
   ```powershell
   uvicorn app.main:app --reload
   ```

2. **Try the protected route** (Swagger at http://localhost:8000/docs):
   - Get a token: **POST /api/v1/auth/login** with body `{"email": "you@example.com", "password": "secret123"}` (or use register). Copy the **access_token** from the response.
   - Click **Authorize** (lock icon). In the **Value** field (Bearer), paste **only** the access_token — no username/password. Click Authorize.
   - Call **GET /api/v1/auth/me**. You should get 200 and `{"id": 1, "email": "you@example.com"}`.
   - Click **Authorize** again and log out (clear the token), or call **GET /api/v1/auth/me** without a token. You should get **401 Unauthorized**.

### What the code does

| File | Purpose |
|------|--------|
| `app/dependencies.py` | `HTTPBearer()` — Swagger shows one "Value" field for the Bearer token. `get_current_user(credentials, session)` — uses `credentials.credentials` as token, decode token, check type "access", load User by id, return User or 401. `CurrentUserDep` — shorthand for routes. |
| `app/api/v1/auth.py` | **GET /api/v1/auth/me** — uses `CurrentUserDep`; returns `UserResponse` (id, email). Only id and email are in the schema so we never expose hashed_password. |

### Verify
- With valid access_token in Authorize: GET /me returns 200 and your user. Without token (or with invalid/expired): 401.

### If something fails
- **401 with valid token** — Ensure you're pasting the **access_token** (not refresh_token). Token may be expired (default 15 min).
- **Swagger Authorize** — Use **HTTPBearer**: in the single "Value" field paste only your access_token (from login/register). Do not use username/password; login expects JSON body, not form data.

---

## Step 5 — Middleware: CORS, request ID, global exception handler

### What you're learning
- **CORS** (Cross-Origin Resource Sharing): Browsers block requests from one origin (e.g. your frontend at `http://localhost:3000`) to another (your API at `http://localhost:8000`) unless the server sends the right headers. We add **CORSMiddleware** so your frontend or mobile app can call the API. Origins come from config (`CORS_ORIGINS`: `*` for all, or a comma-separated list).
- **Request ID**: Every request gets an **X-Request-ID** (from the client if they send it, otherwise we generate one). It’s set on `request.state` and echoed in the response header. Use it for logging and tracing (e.g. when a user reports an error, you can find the request by ID).
- **Global exception handler**: Unhandled exceptions and **HTTPException** are turned into a consistent JSON response with `detail` and optional `request_id`, and the response includes the **X-Request-ID** header so clients can correlate errors.

### What to do

1. **Optional: set CORS in `.env`** (default is `*`):
   ```
   CORS_ORIGINS=*
   ```
   Or restrict to your frontend: `CORS_ORIGINS=http://localhost:3000,https://yourapp.com`

2. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```

3. **Check request ID**:
   - Open http://localhost:8000/docs and call **GET /** (or any route). In the response headers you should see **X-Request-ID** (a UUID).
   - Call **GET /api/v1/auth/me** without a token → 401. The response body includes `"request_id": "<uuid>"` and the response header has **X-Request-ID**.

4. **Check CORS**: From a browser console on another origin (or a simple HTML page on another port), call your API; the response should include CORS headers (e.g. `Access-Control-Allow-Origin`) and the request should succeed if origins are allowed.

### What the code does

| File | Purpose |
|------|--------|
| `app/config.py` | Optional `CORS_ORIGINS` (default `*`) — comma-separated list or `*` for all. |
| `app/middleware.py` | **RequestIDMiddleware**: reads or generates X-Request-ID, sets `request.state.request_id`, adds header to response. |
| `app/main.py` | Adds **RequestIDMiddleware** then **CORSMiddleware** (origins from config). Registers **http_exception_handler** (HTTPException → JSON + request_id) and **unhandled_exception_handler** (any Exception → 500 + request_id). |

### Verify
- Response headers include **X-Request-ID**. 401/500 responses include `request_id` in the body. CORS_ORIGINS in `.env` controls allowed origins.

### If something fails
- **CORS still blocking** — Check `CORS_ORIGINS` (no spaces around `*`, or comma-separated list). Restart the app after changing `.env`.
- **No X-Request-ID** — Middleware runs for all routes; if you don’t see it, check you’re looking at the HTTP response headers (e.g. in browser DevTools Network tab or Swagger response headers).

---

## Step 6 — Rate limiting (Redis, per-IP)

### What you're learning
- **Rate limiting** protects the API from abuse: one client (or bot) can’t send thousands of requests per second. We allow a fixed number of requests per **IP address** per **time window** (e.g. 100 per 60 seconds). If the client exceeds that, we return **429 Too Many Requests** and a **Retry-After** header.
- **Redis** is used because it’s fast and supports atomic **INCR** and **EXPIRE**. Each request does: `INCR ratelimit:ip:<ip>`; on the first request in the window we set `EXPIRE key 60`. If the count is over the limit, we respond with 429 before calling the route. If Redis is down, we **fail open** (allow the request) so the API stays usable.
- **Per-IP** is simple and works for unauthenticated traffic. You can later add per-user limits (using user id in the key) for authenticated routes.

### What to do

1. **Install the new dependency** (venv activated):
   ```powershell
   pip install -r requirements.txt
   ```
   This adds `redis` (async client).

2. **Ensure Redis is running** (Docker stack from Step 0):
   ```powershell
   docker compose up -d
   docker compose ps
   ```
   `smartlens-redis` should be running; `REDIS_URL` in `.env` should be `redis://localhost:6379`.

3. **Optional: tune rate limit in `.env`**:
   ```
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW_SECONDS=60
   ```
   Default is 100 requests per 60 seconds per IP.

4. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```

5. **Test rate limiting** (e.g. with a small limit for quick testing):
   - Temporarily set `RATE_LIMIT_REQUESTS=5` and `RATE_LIMIT_WINDOW_SECONDS=60` in `.env`, restart the app.
   - In Swagger (http://localhost:8000/docs), call **GET /** (or any endpoint) 6 times in a row. The 6th request should return **429 Too Many Requests** with body `{"detail": "Too many requests", "request_id": "..."}` and header **Retry-After: 60**.
   - Wait 60 seconds (or restart Redis to clear keys) and try again — requests should succeed again.
   - Set the limit back to 100 (or leave 5 for dev) as you prefer.

### What the code does

| File | Purpose |
|------|--------|
| `app/config.py` | `RATE_LIMIT_REQUESTS` (default 100), `RATE_LIMIT_WINDOW_SECONDS` (default 60). |
| `app/core/redis_client.py` | Shared async Redis client. `init_redis()` at startup, `close_redis()` at shutdown. `get_redis()` returns the client or None. |
| `app/middleware.py` | **RateLimitMiddleware**: gets client IP (X-Forwarded-For or request.client.host), key `ratelimit:ip:<ip>`, Redis INCR + EXPIRE on first hit; if count > limit return 429 with Retry-After and request_id. Fail open if Redis errors. |
| `app/main.py` | Lifespan: calls `init_redis()` after DB create_all, `close_redis()` before engine dispose. Adds **RateLimitMiddleware** after RequestID. |

### Verify
- With limit 5: 6th request in the same minute returns 429 with Retry-After and request_id. After the window expires, requests succeed again.
- With Redis stopped: requests still succeed (fail open).

### If something fails
- **429 too soon** — Check `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`. Different IPs (e.g. different machine or proxy) have separate limits.
- **Redis connection error at startup** — Ensure `docker compose up -d` and Redis is listening on 6379; `REDIS_URL` in `.env` must match (e.g. `redis://localhost:6379`).
- **No 429 when expected** — Redis might be down (we fail open). Or the limit is high; lower `RATE_LIMIT_REQUESTS` to test.

---

## When you're ready

- After **Step 6**, you have: per-IP rate limiting with Redis, 429 + Retry-After, and fail-open when Redis is unavailable.
- **Day 3 backend is complete.** Next you can move to Day 4 (AI features) or add more endpoints (chat, vision, etc.) using the same patterns (auth, session, rate limit).

We'll add one step at a time so you never have code you haven't learned.
