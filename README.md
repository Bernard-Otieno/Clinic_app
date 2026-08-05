# Clinic Booking API

Backend take-home assessment for Savannah Informatics — a REST API for a small clinic's appointment booking system.

## Documentation

- [Data model](./data-model.md)
- [Technical decisions log](./technical-decisions.md)

## Local setup

1. Clone this repo
2. Create a virtual environment: `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your Supabase connection string (see the file for where to find it)
5. Run the server: `uvicorn app.main:app --reload`
6. Visit `http://localhost:8000/docs` for interactive API docs
7. Visit `http://localhost:8000/health/db` to confirm the database connection works

## Deployment

**Live URL:** https://clinic-booking-api-d23l.onrender.com (redirects to the calendar demo — API docs at `/docs`)

**What triggers a deploy:** merging a pull request into `main`. Pushing directly to `main` also triggers it, since `deploy.yml` runs on any push to that branch — but the normal workflow is PR → CI checks pass → merge.

**Pipeline description:**
- `.github/workflows/ci.yml` runs the full `pytest` suite on every pull request targeting `main`. This is the check that must pass before a PR can be merged in good conscience (not enforced via branch protection, but treated as the gate in practice).
- `.github/workflows/deploy.yml` runs on every push to `main`: it re-runs the test suite as a safety net, and only if that succeeds (via a `needs: test` job dependency) does it call Render's Deploy Hook to trigger the actual deployment. This guarantees broken code never reaches the live URL, regardless of Render's own default behavior.

See [technical-decisions.md](./technical-decisions.md) for the full reasoning behind this setup (entry #4), and [reflection.md](./reflection.md) for the Section 4 AI-usage reflection.

