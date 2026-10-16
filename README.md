# MedCare

A web app for managing your medical needs in one place: find a doctor, book and manage appointments, message your doctors, and keep notes from each visit.

CS4800 Software Engineering with AI, final project (MVP).

> **Demo only.** All doctors are fictional. Don't enter real medical information.

## Features (MVP)

- **Accounts:** sign up, log in, log out (bcrypt password hashing, signed session cookies)
- **Find a doctor:** search by name, specialty, or location, and filter by specialty
- **Appointments:** book, reschedule, and cancel; upcoming vs. past view; no double-booking; Mon–Fri 9:00–5:00 slots
- **Messaging:** message any doctor; each conversation is private to the patient (an automated reply acknowledges the first message, since doctors don't have accounts yet)
- **Visit notes:** keep your own notes on each appointment

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Python, FastAPI |
| Frontend | Server-rendered Jinja2 templates + plain CSS |
| Database | PostgreSQL in production (Neon), SQLite for local dev and tests, via SQLAlchemy |
| CI | GitHub Actions (lint with Ruff, tests with pytest) |
| Hosting | Render (web service) |

## Project structure

```
app/
  main.py            app setup, middleware, error handlers, /health
  config.py          environment-based settings
  database.py        SQLAlchemy engine and session
  models.py          User, Doctor, Appointment, Message
  security.py        password hashing
  deps.py            DB session + current-user dependencies
  seed.py            fictional demo doctors
  templating.py      template rendering helpers
  routers/           auth, doctors, appointments, messages
  templates/         Jinja2 pages
  static/            CSS
tests/               pytest suite (auth, booking rules, privacy, messaging)
.github/workflows/   CI pipeline
render.yaml          Render deployment blueprint
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. With no configuration it uses a local SQLite file (`dev.db`); tables and demo doctors are created on startup.

## Test and lint

```bash
ruff check .
pytest
```

## Deploy

1. **Database:** create a free Postgres project on [Neon](https://neon.tech) and copy its connection string.
2. **Push to GitHub:** create a repo and push this project to `main`. The CI workflow runs on every push and pull request.
3. **Web service:** on [Render](https://render.com), create a new Blueprint (or Web Service) from the GitHub repo. `render.yaml` provides the build and start commands.
4. **Environment variables** (Render dashboard → Environment):
   - `DATABASE_URL`: the Neon connection string
   - `SECRET_KEY`: a long random string (the blueprint generates one)
   - `COOKIE_SECURE`: `1`
5. Render builds and deploys automatically on each push to `main`. The public URL looks like `https://medcare.onrender.com`.

Free Render instances typically sleep when idle, so the first request after a quiet period can be slow.

## Environment variables

See `.env.example`.

## Known limitations / next steps

- Doctors don't log in yet, so there are no real replies or doctor-authored visit notes
- No email or SMS notifications
- Single fixed set of appointment hours for every doctor
- No password reset
