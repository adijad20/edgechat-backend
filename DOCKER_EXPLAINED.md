# Docker in This Project — What Problem It Solves and How It Works

A step-by-step explanation for someone new to backend/Docker.

---

## 1. The Problem Docker Solves

### Without Docker: "It works on my machine"

To run EdgeChat Backend on your laptop you need:

- **Python 3.11** installed
- **PostgreSQL** installed and running
- **MongoDB** installed and running  
- **Redis** installed and running
- Your **.env** with the right `DATABASE_URL`, `MONGODB_URL`, `REDIS_URL`
- Then: `pip install -r requirements.txt` and `uvicorn app.main:app`

If a teammate (or a server) has:

- Different Python version
- Different OS (Windows vs Linux vs Mac)
- Postgres/Mongo/Redis installed differently (or not at all)
- Different ports or passwords

…your app might **not** run there. You’d have to give long setup instructions and debug their environment.

### What we want instead

- **One standard way to run the whole app**: "Run these two commands and everything works."
- **Same environment everywhere**: Your laptop, CI, production server all run the same stack.
- **Isolation**: The app and its databases don’t mess with your system (or each other) except where we choose (e.g. ports, volumes).

**Docker** gives you that: you describe the environment and how to run the app; Docker builds and runs it in **containers**.

---

## 2. Core Ideas (Minimal)

- **Image** = a snapshot of a filesystem + how to run one process (e.g. "Python 3.11 + our code + run uvicorn"). It doesn’t run by itself.
- **Container** = one running instance of an image. Many containers can be created from the same image.
- **Dockerfile** = recipe to **build** an image (install OS bits, Python, deps, copy code, set the command).
- **docker-compose** = a file that says "run several containers (app, postgres, mongo, redis), wire them together, and use the same env."

So:

- **Dockerfile** → build **one image** (your FastAPI app).
- **docker-compose** → run **several containers** from images (app + postgres + mongodb + redis), with networks and env so they can talk.

---

## 3. How It Works in This Project — Step by Step

### Step 1: Building the app image (Dockerfile)

When you run `docker-compose up --build` (or `docker build -t edgechat-backend .`), Docker reads **Dockerfile** and does this:

| Line in Dockerfile | What Docker does |
|--------------------|------------------|
| `FROM python:3.11-slim` | Start from an existing image that already has Python 3.11 on a minimal Linux. You don’t install Python yourself. |
| `WORKDIR /app` | Use `/app` as the current directory inside the container. |
| `COPY requirements.txt .` | Copy only `requirements.txt` from your project into the image. |
| `RUN pip install -r requirements.txt` | Inside the image, run `pip install` so all dependencies are installed. This is isolated from your laptop’s Python. |
| `COPY . .` | Copy the rest of your project (code) into `/app`. (What gets copied is affected by `.dockerignore` — see below.) |
| `RUN useradd ...` and `USER appuser` | Create a non-root user and run the app as that user (security good practice). |
| `EXPOSE 8000` | Document that the app listens on port 8000 (doesn’t open the port by itself; `docker-compose` does that). |
| `CMD ["uvicorn", ...]` | When the container **starts**, run this command (start the FastAPI app). |

**Result:** You get an **image** that contains:

- A fixed Linux + Python 3.11
- Your dependencies
- Your code
- The command to run (uvicorn)

No matter who builds this image (you, a teammate, CI, production), they get the **same** app environment.

---

### Step 2: Running the full stack (docker-compose)

**docker-compose.yml** describes **four services** (four containers):

1. **app** — your FastAPI app (built from the Dockerfile).
2. **postgres** — PostgreSQL database (from the official `postgres:16-alpine` image).
3. **mongodb** — MongoDB (from the official `mongo:7` image).
4. **redis** — Redis (from the official `redis:7-alpine` image).

When you run `docker-compose up --build`:

1. **Network:** Docker creates a private network. Every service gets a **hostname** equal to its **service name** (`app`, `postgres`, `mongodb`, `redis`). So from the app container, you connect to Postgres at `postgres:5432`, not `localhost:5432`.
2. **Environment:** The **app** container gets env vars like:
   - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/postgres`  
     → "Use hostname `postgres`, port 5432, user postgres, password postgres, database postgres."
   - `MONGODB_URL=mongodb://mongodb:27017`  
     → "Use hostname `mongodb`, port 27017."
   - `REDIS_URL=redis://redis:6379/0`  
     → "Use hostname `redis`, port 6379, DB 0."
3. **Start order:** `depends_on: [postgres, mongodb, redis]` means Docker starts Postgres, Mongo, and Redis first, then the **app**. The app can then connect to them as soon as it starts.
4. **Ports:** `ports: ["8000:8000"]` means: "Map port 8000 **inside** the app container to port 8000 **on your laptop**." So when you open `http://localhost:8000`, traffic goes to the app container.

So Docker is:

- **Packaging** your app and its runtime (Dockerfile → image).
- **Orchestrating** several containers (app + DBs) with one command (docker-compose).
- **Isolating** them (they see their own filesystem and network) while still exposing ports and volumes you define.

---

## 4. What Are Volumes For?

Containers are **ephemeral**: if you remove a container, everything written inside it (files, databases) is gone by default. For databases we want **data to persist** across restarts and container re-creates.

**Volumes** are named storage that Docker manages. They live **outside** the container. You **mount** a volume into a path inside the container. Whatever the process writes to that path is stored in the volume, not only in the container.

In your **docker-compose.yml**:

```yaml
postgres:
  volumes: ["postgres_data:/var/lib/postgresql/data"]
```

- **postgres_data** is a volume (declared at the bottom: `postgres_data: {}`).
- **/var/lib/postgresql/data** is where PostgreSQL inside the container stores its data.
- So: "Use the volume `postgres_data` for that directory."

**Effect:**

- First run: Postgres starts, creates databases/tables, writes them into `postgres_data`.
- You run `docker-compose down` then `docker-compose up`: new Postgres container, but it mounts the **same** `postgres_data` → your data is still there.
- Without the volume, every `docker-compose up` would start with an **empty** database.

Same idea for:

- **mongo_data** → MongoDB’s data directory (`/data/db`)
- **redis_data** → Redis’s data directory (`/data`)

So:

- **Volumes = persistent storage for containers.**  
- They solve: "When I restart or recreate the container, I don’t want to lose the database (or other important files)."

---

## 5. What Does .dockerignore Do?

When the Dockerfile runs `COPY . .`, Docker takes the **build context**: everything in the directory where you run `docker build` (usually the project root). By default it would copy:

- Your code
- **venv/** (huge, and not needed in the image)
- **.env** (secrets; you don’t want them baked into the image)
- **.git/** (history; not needed to run the app)
- **__pycache__**, **.pytest_cache**, **.coverage**, etc.

That makes the context slow to send to Docker and can make the image bigger or less secure.

**.dockerignore** works like **.gitignore**: it lists files or folders that should **not** be sent as part of the build context. So when Docker runs `COPY . .`, it **excludes** what’s in `.dockerignore`.

In your project:

| Entry in .dockerignore | Why exclude it |
|------------------------|----------------|
| `venv` | Virtual env is for your laptop. In the image we run `pip install -r requirements.txt` instead. Copying venv would be huge and wrong. |
| `.env` | Contains secrets. We don’t want them baked into the image. The app container gets env from `docker-compose` (environment / env_file) at **runtime**. |
| `.git` | Not needed to run the app; keeps context smaller. |
| `__pycache__`, `*.pyc` | Generated bytecode; not needed and can be recreated. |
| `.pytest_cache`, `.coverage`, `htmlcov` | Test artifacts; not needed in the runtime image. |
| `*.md` | Docs; not needed to run the server. |
| `.github` | CI workflows; not needed inside the app container. |

So:

- **.dockerignore = "When building the image, don’t send these files."**  
- Result: faster builds, smaller context, no venv or secrets in the image.

---

## 6. Quick Mental Model

| Concept | One-line meaning |
|--------|-------------------|
| **Docker** | Run apps in isolated boxes (containers) with a fixed environment. |
| **Dockerfile** | Recipe to build one image (OS + runtime + your app + start command). |
| **Image** | Snapshot of that environment; used to create containers. |
| **Container** | A running instance of an image. |
| **docker-compose** | Run several containers (app + DBs), with one network, env, and ports. |
| **Volumes** | Persistent storage attached to containers (e.g. so DB data survives restarts). |
| **.dockerignore** | Don’t send these files when building the image (faster, smaller, safer). |

Together: **Docker** gives you a single, repeatable way to run the whole stack (app + Postgres + Mongo + Redis) the same way on your machine and elsewhere; **volumes** keep database data; **.dockerignore** keeps builds clean and secure.
