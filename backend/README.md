# Attachify — Backend

FastAPI backend for Attachify. This is Phase 0 of the roadmap in
[`../docs/attachify-srs-technical-design.md`](../docs/attachify-srs-technical-design.md):
repo structure, database schema, and the auth skeleton. Search, scraping, AI, and
payments land in later phases.

## Setup

1. **Create a virtual environment and install dependencies:**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   # source .venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Create a free Postgres database on [Neon](https://neon.tech)** and copy its
   pooled connection string from the dashboard.

3. **Copy `.env.example` to `.env`** and fill in:
   - `DATABASE_URL` — your Neon connection string. Neon gives you a `postgresql://…`
     URL; change the prefix to `postgresql+asyncpg://` for this backend.
   - `SECRET_KEY` — any long random string, e.g. generate one with:
     ```bash
     python -c "import secrets; print(secrets.token_urlsafe(48))"
     ```

4. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

6. Open `http://127.0.0.1:8000/docs` for the interactive API docs, generated
   automatically from the code.

## What's real vs. what's pending

- Register, login, refresh, forgot/reset password, and delete account are fully
  implemented and ready to use.
- Google sign-in (`POST /api/v1/auth/google`) is fully implemented but returns a 501
  until `GOOGLE_CLIENT_ID` is set in `.env` — get one from the
  [Google Cloud Console](https://console.cloud.google.com/).
- Password-reset emails currently log to the console (`ConsoleEmailService` in
  `app/services/email_service.py`) instead of sending real mail. Swap in a
  Brevo/Resend-backed implementation once Phase 3 wires up email (see SRS §17) —
  nothing that calls it needs to change.
- Search, opportunities, companies, scraping, AI, and payments land in Phase 1
  onward, per the roadmap in the SRS.

## Notes on the schema

The Phase 0 migration (`alembic/versions/0001_initial_schema.py`) creates every
core directory/application table from SRS §8 — courses, companies, users,
opportunities, saved opportunities, resumes, cover letters, payments, applications,
reviews, and alert subscriptions. The AI-specific tables (chat history, opportunity
embeddings) are deferred to a Phase 2 migration, since they need the `pgvector`
extension, which isn't worth adding before the AI toolkit actually needs it.

## Project layout

See SRS §19 for the full intended structure as the project grows.
