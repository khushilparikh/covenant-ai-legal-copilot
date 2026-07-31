# Troubleshooting

Detailed local-setup notes, kept separate from the main `README.md` so
the repo's front page stays focused on the project itself. This covers
every environment issue we've hit and fixed while setting this up on
Windows.

## Before you run anything: check where you actually are

After cloning or extracting, run `dir` (or `ls`) before typing any other
command. You want to be at the level where `dir` shows `covenant-backend`
and `covenant-frontend` directly.

**Easiest way to avoid path confusion:** in VS Code's file explorer
sidebar, right-click the `covenant-backend` folder itself → **"Open in
Integrated Terminal"**. That opens a terminal already positioned exactly
inside it. Do the same for `covenant-frontend` in a second terminal.

If you're already inside `covenant-backend` (check the terminal prompt),
don't `cd covenant-backend` again — that's the single most common mistake
here and produces a `Cannot find path ... because it does not exist`
error even though nothing is actually wrong.

## setup.ps1 walkthrough

Run from inside `covenant-backend`:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

It will:
1. Find a compatible Python (3.11 or 3.12) via `py -0`
2. Create `venv/` if it doesn't exist
3. Install all dependencies from `requirements.txt`
4. Download the spaCy language model
5. Create `.env` from `.env.example` and open it in Notepad — edit
   `DATABASE_URL` with your real Postgres password, save, close, then
   press Enter in the terminal to continue
6. Train the clause classifier and risk scoring models (prints real
   accuracy/R² numbers)
7. Create database tables and seed a demo account

It's safe to re-run if it fails partway — it detects an existing
`venv`/`.env` and skips recreating them.

*(If PowerShell refuses to run any script:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or prefix
individual commands with `powershell -ExecutionPolicy Bypass -File`.)*

## Known environment issues and fixes

| Symptom | Cause | Fix |
|---|---|---|
| scikit-learn/scipy build errors, or `ImportError: cannot import name '_ccallback_c'` | Python 3.13/3.14 — no prebuilt wheels yet, or a corrupted partial install | Use Python 3.11/3.12: `py -3.12 -m venv venv` |
| `ModuleNotFoundError` for several packages one at a time | `pip install -r requirements.txt` didn't fully complete, often silently | Re-run the full install and scroll through the output for red `ERROR:` lines |
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | passlib 1.7.4 is incompatible with bcrypt 4.1+ | Already pinned (`bcrypt==4.0.1`) in `requirements.txt` |
| `email-validator is not installed` | Missing dependency for Pydantic's `EmailStr` | Already pinned in `requirements.txt` |
| Login fails with "value is not a valid email address" | `.local` is a reserved special-use TLD, rejected by email-validator | Demo account uses `admin@covenant.dev`, not `.local` |
| Frontend goes completely blank after a failed action | FastAPI validation errors return `detail` as an array of objects, not a string — rendering it directly crashed React | Fixed via a shared `getErrorMessage()` helper + a top-level error boundary |
| Upload returns 500, browser console shows a CORS error | Misleading symptom — an unhandled backend exception cut the response short before CORS headers were sent. Common cause: Ollama model not pulled | Check the **backend terminal** for the real traceback; run `ollama pull llama3:8b` |
| `.\setup.ps1` throws "is not digitally signed" / script execution errors | Windows PowerShell execution policy blocks unsigned scripts | `powershell -ExecutionPolicy Bypass -File .\setup.ps1` |
| `ValueError: invalid literal for int() ... 'passwordlocalhost:5432'` | Missing `@` separator in `DATABASE_URL` in `.env` | Must read exactly `postgresql+psycopg2://postgres:PASSWORD@localhost:5432/covenant` |
| Adding the `plan`/billing feature to an existing database | `Base.metadata.create_all()` only creates missing tables, never alters existing ones | `psql -U postgres -d covenant -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR NOT NULL DEFAULT 'free';"` |

If you hit something not on this list, the most useful thing you can
paste is the **full traceback from the backend terminal** (not just the
browser console) — that's what actually identifies the cause instead of
just the symptom.
