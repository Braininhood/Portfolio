# MultiBook – GitHub Setup Guide

This guide helps you put MultiBook on GitHub in a clean, professional way and keep the repository structure correct.

---

## 1. Prerequisites

- **Git** installed ([git-scm.com](https://git-scm.com/)).
- **GitHub account** ([github.com](https://github.com/)).
- Project already in a folder (e.g. `d:\MultiBook`).

---

## 2. Ensure correct project structure

Your repo should look like this:

```
MultiBook/
├── .gitignore              # Root ignore (env, venv, node_modules, .next, etc.)
├── README.md                # Main project readme
├── GITHUB_SETUP.md          # This file
├── start-dev.ps1            # Dev scripts (optional)
├── stop-dev.ps1
├── backend/                 # Django app
│   ├── .gitignore           # Backend-specific ignores
│   ├── requirements.txt
│   ├── env.example          # Copy to .env (do not commit .env)
│   ├── config/
│   ├── apps/
│   └── manage.py
├── frontend/                # Next.js app
│   ├── .gitignore           # Frontend-specific ignores
│   ├── package.json
│   ├── .env.example         # Copy to .env.local (do not commit)
│   └── app/
└── docs/                    # Documentation
    ├── README.md            # Docs index
    ├── AWS_DEPLOYMENT_GUIDE.md
    └── ...                  # Other implementation guides
```

**Important:**

- **Never commit** `.env`, `.env.local`, or any file with secrets. The root and app `.gitignore` files already exclude them.
- **Commit** `env.example` / `.env.example` (no secrets, only variable names and placeholders).

---

## 3. First-time Git setup (if the folder is not a repo yet)

In PowerShell (or Git Bash), from the project root:

```powershell
cd d:\MultiBook

# Initialize repository (only if not already a git repo)
git init

# Set default branch name to main
git branch -M main
```

If the folder is already a Git repo (you have a `.git` folder), skip `git init` and just ensure you’re on `main`:

```powershell
git status
git branch -M main   # Rename current branch to main if needed
```

---

## 4. Check what will be committed

Make sure no secrets or build artifacts are staged:

```powershell
# See what’s ignored (should include .env, venv, node_modules, .next)
git status

# If you see .env or venv/ or node_modules/ in “to be committed”, remove them:
git reset HEAD .env backend/.env frontend/.env.local 2>$null
# And ensure .gitignore is correct (see root .gitignore)
```

Root `.gitignore` should already exclude:

- `.env`, `.env.local`, `venv/`, `node_modules/`, `.next/`, `__pycache__/`, `staticfiles/`, `media/`, `db.sqlite3`, etc.

---

## 5. Stage and commit

```powershell
# Stage all files (respecting .gitignore)
git add .

# Review what will be committed
git status

# Commit with a clear message
git commit -m "Initial commit: MultiBook booking system (Django + Next.js)"
```

Use a different message if this is not the first commit (e.g. “Add GitHub setup and AWS deployment docs”).

---

## 6. Create the repository on GitHub

1. Go to [github.com](https://github.com/) and sign in.
2. Click **“+”** → **“New repository”**.
3. **Repository name:** e.g. `MultiBook` (or `multibook`).
4. **Description:** e.g. `MultiBook booking system – Django + Next.js`.
5. **Public** (or Private if you prefer).
6. **Do not** add a README, .gitignore, or license here (you already have them in the project).
7. Click **Create repository**.

---

## 7. Connect local repo and push

GitHub will show commands; use these (replace with your GitHub username and repo name):

```powershell
# Add GitHub as remote (use HTTPS or SSH)
git remote add origin https://github.com/YOUR_USERNAME/MultiBook.git

# If you prefer SSH (after adding your SSH key to GitHub):
# git remote add origin git@github.com:YOUR_USERNAME/MultiBook.git

# Push main branch and set upstream
git push -u origin main
```

If the remote `origin` already exists but points to another URL:

```powershell
git remote set-url origin https://github.com/YOUR_USERNAME/MultiBook.git
git push -u origin main
```

If GitHub created a branch (e.g. with a README), you may need:

```powershell
git pull origin main --allow-unrelated-histories
# Resolve any conflicts, then:
git push -u origin main
```

---

## 8. Documentation layout

Implementation and status docs are in **`docs/`**; the root keeps only the main README, solution docs, and this setup guide. See `docs/README.md` for the full index.

---

## 9. Branch and protection (recommended for teams)

- **Default branch:** `main`.
- **Branch protection (optional):**  
  Repo → **Settings** → **Branches** → **Add rule** for `main`: require pull request reviews, require status checks, do not allow force push.

---

## 10. Summary checklist

- [ ] Root `.gitignore` excludes `.env`, `venv/`, `node_modules/`, `.next/`, `__pycache__/`, `staticfiles/`, `media/`, `db.sqlite3`.
- [ ] No `.env` or real secrets committed; only `env.example` / `.env.example` in repo.
- [ ] `git add .` and `git status` show no sensitive or build-only files.
- [ ] GitHub repo created (no extra README/.gitignore if you already have them).
- [ ] `git remote add origin` and `git push -u origin main` done.
- [ ] Docs organized in `docs/` (see `docs/README.md`).

After this, your project is on GitHub in a correct, professional structure. For deployment, follow [docs/AWS_DEPLOYMENT_GUIDE.md](docs/AWS_DEPLOYMENT_GUIDE.md).
