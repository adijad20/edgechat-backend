# Day 4 — EdgeChat Backend: AI Integration + Core Features (Step-by-Step)

We add Google Gemini and build Chat, Vision, and Summarize APIs — one step at a time, like Day 2 and Day 3.

---

## Concepts You'll Meet

| Term | What it is |
|------|------------|
| **Gemini API** | Google's generative AI (text, chat, vision). We call it from our backend so mobile clients get AI without holding API keys. |
| **AI service layer** | A single module that wraps the Gemini SDK: error handling, timeouts, one place to change model or provider. |
| **MongoDB** | NoSQL store for chat history and vision results. Flexible schema fits variable-length conversations. |
| **Cursor / pagination** | List endpoints return a page of items plus a cursor (or offset) so clients can request "next page" without loading everything. |

---

## The Steps (Roadmap)

- **Step 1** — Gemini SDK + API key, AI service wrapper, test endpoint.
- **Step 2** — MongoDB connection + chat storage (conversations and messages).
- **Step 3** — Chat API: create conversation, send message (Gemini + context), list conversations (paginated).
- **Step 4** — Redis caching for identical AI prompts (optional).
- **Step 5** — Vision API: upload image, Gemini vision, return analysis.
- **Step 6** — Summarize API: text and URL summarization.
- **Step 7** — Usage tracking (log API calls per user for `/usage/me`). ✓ You are here

Do **Step 1** first. When you're comfortable, say **"ready for Step 2"** and we'll add the next part.

---

## Step 1 — Gemini SDK + AI service + test endpoint

### What you're learning
- **Gemini API**: You get a key from [Google AI Studio](https://aistudio.google.com/), put it in `.env` as `GEMINI_API_KEY`, and call the API from the backend. The mobile app never sees the key.
- **AI service layer**: One module (`app/services/ai_service.py`) that creates the Gemini client and exposes a simple function like `generate_text(prompt) -> str`. Later we'll add chat-with-history and vision here. If the API fails (timeout, quota), we handle it in one place.
- **Test endpoint**: A single route (e.g. **POST /api/v1/ai/complete**) that accepts `{"prompt": "Hello"}` and returns `{"text": "<Gemini reply>"}` so you can verify the integration without building chat yet.

### What to do

1. **Get a Gemini API key** (if you don't have one):
   - Go to https://aistudio.google.com/
   - Sign in, create or open a project, and get an API key.
   - Add it to your `.env`:
   ```
   GEMINI_API_KEY=your-actual-key-here
   ```

2. **Install the SDK** (venv activated):
   ```powershell
   pip install -r requirements.txt
   ```
   (We add `google-genai` to requirements.txt in this step.)

3. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```

4. **Try the test endpoint** (Swagger at http://localhost:8000/docs):
   - **POST /api/v1/ai/complete** — body: `{"prompt": "Say hello in one sentence."}`.
   - You should get 200 and `{"text": "..."}` with Gemini's reply.
   - If `GEMINI_API_KEY` is missing or invalid, you'll get a clear error (e.g. 503 or 401).

### What the code does

| File | Purpose |
|------|--------|
| `app/config.py` | Already has `GEMINI_API_KEY` (optional). We add `GEMINI_MODEL` (e.g. `gemini-2.0-flash`) so you can switch models without code change. |
| `app/services/ai_service.py` | Creates Gemini client from config. `generate_text(prompt: str) -> str`: calls Gemini, returns reply text; raises or returns error message on failure. |
| `app/schemas/ai.py` | Pydantic: `CompleteRequest` (prompt: str), `CompleteResponse` (text: str). |
| `app/api/v1/ai.py` | Router with **POST /complete**: body `CompleteRequest`, calls `ai_service.generate_text`, returns `CompleteResponse`. No auth required for this test route (we can protect it in a later step). |
| `app/main.py` | `include_router(ai_router.router, prefix="/api/v1")` so the route is **POST /api/v1/ai/complete**. |

### Verify
- POST /api/v1/ai/complete with `{"prompt": "Hello"}` returns 200 and a `text` field with Gemini's response.
- With empty or wrong `GEMINI_API_KEY`, you get a non-2xx response with a clear message.

### If something fails
- **ModuleNotFoundError: google.genai** — Run `pip install -r requirements.txt` (google-genai added in Step 1).
- **503 or "API key invalid"** — Check `.env`: `GEMINI_API_KEY` set and no extra spaces. Restart the app after changing `.env`.
- **429 RESOURCE_EXHAUSTED / quota** — Free tier has limits. Wait a minute and retry, or try **GEMINI_MODEL=gemini-2.0-flash** with **GEMINI_API_VERSION=v1beta** (may have different quota).
- **404 NOT_FOUND (model not found)** — The model may not exist for the API version. Default is **GEMINI_API_VERSION=v1alpha** and **GEMINI_MODEL=gemini-1.5-flash**. If you get 404, try **GEMINI_API_VERSION=v1beta** and **GEMINI_MODEL=gemini-2.0-flash** in `.env`.

---

## Step 2 — MongoDB connection + chat storage (conversations and messages)

### What you're learning
- **MongoDB** stores chat history: flexible documents (one per conversation) with an array of messages. No fixed schema for message count or length.
- **Motor** is the async MongoDB driver for Python. We connect at startup, get a database, and use collections (e.g. `conversations`) to insert and query.
- **Chat storage**: One document per conversation: `user_id`, `created_at`, `updated_at`, `messages: [{ role: "user"|"model", content: "..." }]`. We expose: create conversation, get by id, append messages, list (paginated), delete.

### What to do

1. **Install the new dependency** (venv activated):
   ```powershell
   pip install -r requirements.txt
   ```
   This adds `motor` (async MongoDB driver).

2. **Ensure MongoDB is running** (Docker stack from Step 0):
   ```powershell
   docker compose up -d
   docker compose ps
   ```
   `smartlens-mongo` should be running; `MONGODB_URL` in `.env` should be `mongodb://localhost:27017`.

3. **Run the app**:
   ```powershell
   uvicorn app.main:app --reload
   ```

4. **Check MongoDB health**:
   - Open http://localhost:8000/api/v1/health/mongo — you should see `{"status":"ok","mongo":"connected"}`.
   - If 503, check that MongoDB is up and `MONGODB_URL` is correct in `.env`.

### What the code does

| File | Purpose |
|------|--------|
| `app/core/mongo.py` | `init_mongo()` / `close_mongo()` at startup/shutdown. `get_database()` returns the `edgechat` database. Uses Motor `AsyncIOMotorClient`. |
| `app/services/chat_storage.py` | `create_conversation(user_id)` → new doc, returns id. `get_conversation(id, user_id)`, `append_messages(id, user_id, messages)`, `list_conversations(user_id, limit, skip)`, `delete_conversation(id, user_id)`. Collection: `conversations`. |
| `app/main.py` | Lifespan: `init_mongo()` after Redis, `close_mongo()` in finally. **GET /api/v1/health/mongo** pings MongoDB and returns ok or 503. |

### Verify
- App starts; **GET /api/v1/health/mongo** returns 200 and `mongo: connected`. No MongoDB-related errors in logs.

### If something fails
- **503 mongo not initialized** — Ensure `init_mongo()` runs in lifespan (no exception before it). Check imports.
- **503 connection failed** — `docker compose up -d`, MongoDB on 27017, `MONGODB_URL=mongodb://localhost:27017` in `.env`.

---

## Step 3 — Chat API: create conversation, send message (Gemini + context), list conversations (paginated)

### What you're learning
- **Chat API**: All routes require auth (Bearer token). You create a conversation, send messages, and get AI replies with full conversation context sent to Gemini. Messages are stored in MongoDB.
- **Multi-turn**: The AI service's `generate_chat(messages)` sends the full history (list of `{role, content}`) to Gemini so the model can refer to earlier turns. Each new user message is appended, then the model reply is generated and both are stored.
- **Pagination**: List conversations and get messages support `limit` and `skip`; responses include `has_more` so the client can request the next page.

### What to do

1. **Run the app** (MongoDB + Gemini already set up):
   ```powershell
   uvicorn app.main:app --reload
   ```

2. **Get a token** (Swagger or curl): **POST /api/v1/auth/login** with `{"email": "...", "password": "..."}`. Copy the `access_token`.

3. **Authorize**: In Swagger, click **Authorize**, paste the access token in the Value field, click Authorize.

4. **Try the Chat API** (http://localhost:8000/docs):
   - **POST /api/v1/chat/conversations** — creates a conversation, returns `{"id": "..."}`.
   - **POST /api/v1/chat/conversations/{id}/messages** — body `{"content": "Hello, what can you do?"}`. You get back `user_message` and `model_message` (Gemini's reply). Send another message in the same conversation — the reply will have context from the first turn.
   - **GET /api/v1/chat/conversations** — list your conversations (query params: `limit`, `skip`). Response has `conversations` and `has_more`.
   - **GET /api/v1/chat/conversations/{id}/messages** — message history (params: `limit`, `skip`).
   - **DELETE /api/v1/chat/conversations/{id}** — delete a conversation (204 No Content).

### What the code does

| File | Purpose |
|------|--------|
| `app/services/ai_service.py` | `generate_chat(messages: list[{role, content}])` — builds Gemini `Content` list from history, calls `generate_content`, returns reply text. Same 429/404 handling as `generate_text`. |
| `app/services/chat_storage.py` | Added `get_messages(conv_id, user_id, limit, skip)` → `(messages_slice, has_more)` for paginated message history. |
| `app/schemas/chat.py` | Pydantic: CreateConversationResponse, SendMessageRequest/Response, MessageItem, ConversationItem, ListConversationsResponse, GetMessagesResponse (with has_more). |
| `app/api/v1/chat.py` | Router under `/chat`: POST/GET conversations, POST/GET messages, DELETE conversation. All use `CurrentUserDep`. Send message: load conv, call `generate_chat(history + [user_msg])`, append user + model messages, return both. |
| `app/main.py` | `include_router(chat_router.router, prefix="/api/v1")` so routes are under `/api/v1/chat/...`. |

### Verify
- Create conversation → send message → get AI reply. Send a second message in the same conversation and confirm the reply uses context (e.g. "As I mentioned..."). List conversations and get messages return paginated data with `has_more` when applicable.

### If something fails
- **401 on chat routes** — Authorize in Swagger with your access_token (from login).
- **404 Conversation not found** — Wrong id or conversation belongs to another user. Use the id from create or list.
- **503 on send message** — Gemini API error (key, model, or quota). Check GEMINI_API_KEY and try again later.

---

## Step 7 — Usage tracking (log API calls per user for `/usage/me`)

### What you're learning
- **Usage tracking**: Every authenticated API request (valid Bearer token) is logged in PostgreSQL: one row per request with `user_id`, `path`, `method`, `created_at`. So you can show each user their usage and enforce limits later.
- **Middleware**: We decode the JWT in a middleware (no need to hit the DB for the user). After the request is handled we append a row to `api_usage`. Logging errors are ignored so the API response is never broken.
- **GET /usage/me**: Returns the current user's stats: `total_requests`, `requests_last_24h`, `requests_last_7d` (counts from the `api_usage` table).

### What to do

1. **Run the app** (no new deps). The `api_usage` table is created on startup (Base.metadata.create_all).
   ```powershell
   uvicorn app.main:app --reload
   ```

2. **Authorize** in Swagger and call any protected endpoint a few times (e.g. GET /api/v1/chat/conversations, POST /api/v1/chat/conversations, etc.).

3. **GET /api/v1/usage/me** — You should see `total_requests`, `requests_last_24h`, `requests_last_7d`. Counts increase as you make authenticated requests.

### What the code does

| File | Purpose |
|------|--------|
| `app/models/usage.py` | **ApiUsage** table: id, user_id (FK to users), path, method, created_at. |
| `app/services/usage_service.py` | `log_usage(user_id, path, method)` — inserts one row (uses its own session). `get_usage_stats(session, user_id)` — returns total, last_24h, last_7d counts. |
| `app/middleware.py` | **UsageLogMiddleware**: reads Bearer token, decodes with `decode_token`; if type=access, sets user_id. After `call_next`, if user_id set, calls `log_usage`. Errors in logging are ignored. |
| `app/api/v1/usage.py` | **GET /usage/me** — uses CurrentUserDep and SessionDep, returns `get_usage_stats(session, current_user.id)`. |
| `app/main.py` | Adds **UsageLogMiddleware** and **usage_router** (prefix /api/v1). |

### Verify
- Make a few authenticated requests, then **GET /api/v1/usage/me**. Response shows counts; total_requests and requests_last_24h reflect recent calls.

### If something fails
- **api_usage table missing** — Restart the app so `create_all` runs (and ensure `app.models.usage` is imported via `app.models` so the model is registered).
- **Counts always 0** — Ensure you're sending a valid Bearer token (Authorize in Swagger). Only authenticated requests are logged.

---

## When you're ready

- After **Step 7**, you have: usage logging for authenticated requests and **GET /usage/me** for per-user stats. Steps 4–6 (caching, Vision, Summarize) can be added later.
- Reply with **"ready for Step 4"**, **"ready for Step 5"**, or **"ready for Step 6"** when you want to add those features.

We'll add one step at a time so you never have code you haven't learned.
