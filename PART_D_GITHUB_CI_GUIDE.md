# Part D — Push to GitHub and See CI Run (Step-by-Step)

This guide assumes you have never pushed a repo to GitHub before. Follow the steps in order.

---

## Before you start

- **Git** installed on your machine (check: open a terminal and run `git --version`).
- A **GitHub account**. If you don’t have one: go to [github.com](https://github.com), click **Sign up**, and create an account.
- Your project folder: `c:\Users\IN009361\Desktop\BackendProjects\smartlens-ai` (or wherever your project lives; the repo can be named `edgechat-backend`).

---

## Step 1: Create a new repository on GitHub (empty, no files)

1. Log in to [github.com](https://github.com).
2. In the top-right, click the **+** icon → **New repository**.
3. Fill in:
   - **Repository name:** `edgechat-backend` (or any name you like, e.g. `my-backend`).
   - **Description:** optional, e.g. "EdgeChat Backend – FastAPI, Postgres, Mongo, Redis".
   - **Public** is fine for learning.
   - **Do not** check "Add a README file", "Add .gitignore", or "Choose a license". We want an **empty** repo so we push our existing code.
4. Click **Create repository**.

You’ll see a page with "Quick setup" and a URL like:
`https://github.com/YOUR_USERNAME/edgechat-backend.git`

Keep this page open or copy that URL; you’ll need it in Step 4.

---

## Step 2: Open a terminal in your project folder

- **Windows:** Open PowerShell or Command Prompt.
- Go to your project:
  ```bash
  cd c:\Users\IN009361\Desktop\BackendProjects\smartlens-ai
  ```
- Confirm you’re in the right place (you should see `app`, `tests`, `docker-compose.yml`, etc.):
  ```bash
  dir
  ```

---

## Step 3: Initialize Git and make the first commit (if not already a Git repo)

Run these one by one. If you already have a `.git` folder (e.g. you ran `git init` before), skip the `git init` line and only add/commit.

**3.1 — Initialize Git (only if this folder is not yet a Git repo)**  
Check first:
```bash
git status
```
- If you see `fatal: not a git repository`, then run:
  ```bash
  git init
  ```
- If you see `On branch main` or `On branch master` and a list of files, you already have a repo; skip `git init`.

**3.2 — Add all files (respecting .gitignore)**  
We have a `.gitignore` so `venv`, `.env`, `__pycache__`, etc. won’t be added.
```bash
git add .
```

**3.3 — See what will be committed**  
```bash
git status
```
You should see your code and config (e.g. `app/`, `tests/`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`). You should **not** see `venv/` or `.env` in the list.

**3.4 — Create the first commit**  
```bash
git commit -m "Initial commit: EdgeChat Backend with Day 5 tests and CI"
```

You should see something like: `X files changed, Y insertions(+)`.

---

## Step 4: Connect your folder to GitHub and push

**4.1 — Add the GitHub repo as “remote”**  
Replace `YOUR_USERNAME` and `edgechat-backend` with your GitHub username and repo name from Step 1.
```bash
git remote add origin https://github.com/YOUR_USERNAME/edgechat-backend.git
```
Example: if your username is `johndoe`, then:
```bash
git remote add origin https://github.com/johndoe/edgechat-backend.git
```

If you get `remote origin already exists`, that’s fine; it means the remote was added before. You can check with:
```bash
git remote -v
```

**4.2 — Name your branch (if needed)**  
GitHub expects `main` or `master`. Check your current branch:
```bash
git branch
```
- If you see `* main`, you’re good.
- If you see `* master`, you’re also good (our CI runs on both).
- If the branch has another name (e.g. `master`), you can rename it to `main` if you prefer:
  ```bash
  git branch -M main
  ```

**4.3 — Push to GitHub**  
First push usually needs to “set upstream”:
```bash
git push -u origin main
```
If your default branch is `master`, use:
```bash
git push -u origin master
```

- GitHub may ask you to **log in**. Use your GitHub username and either:
  - A **Personal Access Token** (recommended), or  
  - GitHub’s password flow if still available in your region.
- To create a token: GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)** → **Generate new token**. Give it a name, tick **repo**, generate, then **paste the token** when Git asks for a password (username = your GitHub username).

After a successful push, the GitHub repo page will show your files and commits.

---

## Step 5: See CI run on GitHub Actions

1. On GitHub, open **your repository** (e.g. `github.com/YOUR_USERNAME/edgechat-backend`).
2. Click the **Actions** tab (top menu).
3. You should see a workflow run named **CI** (from the first push). Click it.
4. You’ll see three **jobs**: **lint**, **test**, **docker**.
   - **lint:** runs `ruff check .`
   - **test:** starts Postgres, Mongo, Redis, then runs `pytest -v`
   - **docker:** runs `docker build -t edgechat-backend:ci .`
5. Wait a few minutes. If all three turn **green (✓)**, Part D is done.

If a job fails (red), click the job name, then the failing step, to see the log (e.g. which test failed or which ruff error appeared).

---

## Step 6: Trigger CI again with a new commit (optional)

To see CI run again:

1. Change something small (e.g. add a comment in `app/main.py` or this guide).
2. In the project folder:
   ```bash
   git add .
   git commit -m "Docs: small update"
   git push
   ```
3. Go to GitHub → **Actions**. A new **CI** run should appear and run the same three jobs.

---

## Quick reference

| Step | What to do |
|------|------------|
| 1 | GitHub → New repository → name it → **don’t** add README/.gitignore → Create |
| 2 | Terminal: `cd` to your project folder (e.g. `smartlens-ai` or `edgechat-backend`) |
| 3 | `git init` (if needed) → `git add .` → `git commit -m "Initial commit: ..."` |
| 4 | `git remote add origin https://github.com/YOUR_USERNAME/edgechat-backend.git` → `git push -u origin main` (or `master`) |
| 5 | GitHub → your repo → **Actions** tab → open **CI** run → wait for lint, test, docker to turn green |
| 6 | (Optional) Edit a file → `git add .` → `git commit -m "..."` → `git push` → check Actions again |

---

## If something goes wrong

- **“failed to push” / “Authentication failed”**  
  Use a **Personal Access Token** as the password when Git asks. Make sure the token has **repo** scope.

- **“remote origin already exists”**  
  Run `git remote -v`. If `origin` points to the wrong URL, fix it:
  ```bash
  git remote set-url origin https://github.com/YOUR_USERNAME/edgechat-backend.git
  ```

- **CI “test” job fails**  
  Open the job log; it’s the same `pytest` we run locally. Fix the failing test or env (e.g. dependency version) and push again.

- **CI “lint” job fails**  
  Run locally: `pip install ruff` then `ruff check .` and fix the reported issues, then commit and push.

- **.env was committed by mistake**  
  Don’t fix it by deleting the file and committing (it stays in history). Rotate any secrets that were in `.env`, add `.env` to `.gitignore`, then from the next commit onward it won’t be tracked. For the future, our `.gitignore` already includes `.env`.

Once your first push is done and you’ve seen the **Actions** tab with a green **CI** run, you’ve completed Part D.
