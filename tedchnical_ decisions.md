# Technical Decisions Log — Clinic Booking System

This is a running record of the decisions I made on this project, why I made them, and what I considered instead. Updated as I went — this is the source of truth behind the README's "design decisions" section and the Section 4 AI-reflection writeup.

---

### 1. Backend framework: FastAPI
**Decision:** I chose Python + FastAPI over Django REST Framework or Go.
**Reasoning:** Fast to build within the 3–5 day limit, validates request/response data automatically, and generates interactive API docs for free — useful for demoing to stakeholders without extra tooling.
**Alternatives considered:** Django REST Framework (more built-in structure, but heavier for a 4-table app), Go (steeper learning curve for me to build confidently within the time limit).

### 2. Database: PostgreSQL
**Decision:** I chose PostgreSQL over SQLite.
**Reasoning:** Handles concurrent writes safely — important because the core requirement is preventing two patients from booking the same slot at once. SQLite is file-based and not built for concurrent access.

### 3. Hosting: reusing my existing Render + Supabase accounts
**Decision:** A new, separate Supabase project (Postgres) and a new, separate Render web service, both isolated from my existing projects on those accounts.
**Reasoning:** Supabase's free tier allows 2 active projects per account; Render has no meaningful limit on the number of free web services. I reused infrastructure I was already familiar with, rather than learning a new platform under a deadline.
**Note:** I had to use Supabase's pooled connection string (session or transaction pooler), not the direct connection — Render's servers connect/disconnect frequently, which the pooler is built to handle.

### 4. CI/CD gating: two-stage GitHub Actions pipeline
**Decision:** `ci.yml` runs tests on every pull request. `deploy.yml` runs tests again on push to `main`, and only calls Render's Deploy Hook if the test job succeeds (via a `needs: test` job dependency).
**Reasoning:** Render's default "auto-deploy on push" has no awareness of test results. Turning off Render's auto-deploy and instead triggering deploys via an explicit Deploy Hook, gated behind a passing test job, guarantees broken code never reaches my live URL.
**Alternatives considered:** Relying on GitHub branch protection rules alone (require passing status checks before merge) — simpler, but can be bypassed by a repo admin, so I treated it as a secondary safeguard rather than the primary gate.

### 5. Data model: UUID primary keys
**Decision:** I used UUIDs instead of auto-incrementing integers for all table IDs.
**Reasoning:** Harder to guess/enumerate than sequential integers — a good habit for anything patient-adjacent, even at assessment scale. I've seen sequential IDs leak information in other systems (e.g. `/appointments/47` inviting someone to try `/appointments/48`), so this was an easy call based on experience.

### 6. Data model: no split-shift support for doctors
**Decision:** Each doctor has exactly one continuous working block per weekday.
**Reasoning:** The scenario didn't require split shifts; supporting them would add real complexity to the slot-generation logic for a case that wasn't asked for. I'm documenting this as a known, intentional limitation rather than an oversight.

### 7. Data model: soft-delete for cancelled appointments
**Decision:** Cancelling sets `status = cancelled` rather than deleting the row.
**Reasoning:** Preserves an audit trail — a clinic needs to be able to answer "did this patient have an appointment?" after the fact.

### 8. Double-booking prevention: database-level constraint
**Decision:** A unique index on `(doctor_id, start_time)` scoped to `status = booked`, enforced by PostgreSQL itself.
**Reasoning:** An application-level "check availability, then write" approach has a race-condition gap — two near-simultaneous requests could both pass the check before either writes. A database constraint closes that gap entirely, which mattered more to me than relying on application code alone.

### 9. No separate "Slot" table
**Decision:** Available slots are calculated at request time from `WorkingHours` minus booked `Appointments`, not stored as their own rows.
**Reasoning:** Simpler schema, no risk of slot records drifting out of sync with actual appointments. Trade-off: marginally more computation per availability request, which I judged acceptable at clinic scale.

### 10. Referential integrity: cascade vs. restrict
**Decision:** `working_hours.doctor_id` uses `ON DELETE CASCADE`; `appointments.doctor_id` and `appointments.patient_id` use `ON DELETE RESTRICT`.
**Reasoning:** Working hours have no meaning independent of the doctor they belong to, so deleting a doctor should clean those up automatically. Appointments are historical records — I wanted deleting a doctor or patient to be *blocked* if appointments still reference them, so booking history can never be silently destroyed by an unrelated delete.

### 11. Schema implemented as raw SQL (`schema.sql`), run directly in Supabase's SQL Editor
**Decision:** I hand-wrote the DDL rather than starting from an ORM's auto-generated migration.
**Reasoning:** For a 4-table schema, writing the SQL directly was faster for me and made the exact constraints (partial unique index, check constraints) explicit and easy to review. I'm using Alembic for *future* migrations once the app is running, so schema changes stay version-controlled going forward.

### 12. ORM models mirror the raw SQL exactly, including constraints
**Decision:** `app/models.py` re-declares every constraint from `schema.sql` in SQLAlchemy syntax (check constraints, the doctor/weekday uniqueness rule, and the partial unique index preventing double-booking) — even though the tables already exist in Supabase and these lines don't create anything new.
**Reasoning:** Two purposes: (1) documentation — anyone reading the model file (including me, later) understands the business rules without needing to cross-reference `schema.sql`, and (2) a safety net — if I ever rebuild the database from scratch via SQLAlchemy/Alembic instead of the raw SQL file, these constraints get recreated automatically rather than silently lost.

### 13. `updated_at` auto-stamped via `onupdate=func.now()`
**Decision:** The `Appointment.updated_at` column uses SQLAlchemy's `onupdate=func.now()`, so it's automatically refreshed any time a row is updated through the ORM (e.g. cancelling or rescheduling).
**Reasoning:** Removes the need to manually set this timestamp in every endpoint that modifies an appointment — one less thing for me to forget, one less place for a bug to hide.

### 14. Availability date passed as a query parameter
**Decision:** `GET /doctors/{id}/availability?date=YYYY-MM-DD` rather than `/doctors/{id}/availability/{date}`.
**Reasoning:** REST convention: path parameters identify *which resource* (the doctor), query parameters filter/modify the request (which date to check). This also leaves room for me to add more optional query params later (e.g. a date range) without changing the URL structure.

### 15. Availability matching compares time-of-day, not full timestamps
**Decision:** When filtering out already-booked slots, I compare `.time()` (just the clock time) rather than full datetime objects.
**Reasoning:** The database stores timestamps as timezone-aware, while my generated candidate slots are naive (built from a date + a plain time-of-day). Comparing full datetimes directly would silently never match due to that mismatch. Comparing time-of-day only sidesteps it cleanly, since every appointment in the result set is already filtered to the requested date. **Known limitation:** this assumes a single-timezone clinic (no daylight saving/multi-timezone support) — reasonable for a local clinic booking system, but worth being explicit about.

### 16. Lightweight calendar frontend added as a bonus (not a graded requirement)
**Decision:** A single static HTML/JS page, served directly by my FastAPI app as a static file — rather than a separate frontend project with its own build tooling and deployment.
**Reasoning:** This is a Backend Developer assessment; the frontend isn't graded. I built it primarily to demo the booking logic visually to stakeholders. Keeping it same-origin (served by FastAPI itself) avoided CORS complexity and a second deployment target, minimizing time spent on a non-graded piece.

### 17. Tests run against my real Supabase database, wrapped in a rolled-back transaction
**Decision:** Rather than a separate test database (e.g. Docker Postgres, or SQLite), my tests run against the actual Supabase database, with each test wrapped in a transaction that's rolled back afterward.
**Reasoning:** My models rely on Postgres-specific features (the `UUID` type, the partial unique index enforcing no-double-booking) that SQLite can't replicate, and standing up a separate Postgres via Docker would cost setup time I didn't have much of in a 3–5 day window. The rollback-per-test pattern gives me test isolation (no leftover data, tests don't affect each other) without new infrastructure. **Trade-off:** tests require network access to Supabase to run, and CI needed the connection string available as a secret.

### 18. Root URL redirects to the calendar frontend
**Decision:** `GET /` returns a redirect to `/app/` instead of a bare JSON status message. Interactive API docs remain available separately at `/docs` (FastAPI provides this automatically).
**Reasoning:** The deployed public URL is what stakeholders and reviewers land on first — redirecting to the working calendar demo makes a stronger first impression than a plain `{"status": "ok"}` response, while `/docs` stays one click away for anyone wanting to inspect the API directly.

### 19. `GET /patients/{id}/appointments` filters to upcoming, booked appointments only
**Decision:** Returns only appointments with `status = 'booked'` and `start_time` in the future, sorted soonest-first.
**Reasoning:** Matches the assessment's wording ("upcoming appointments sorted by date") — a patient checking this wants to know what's coming up, not a full historical log including cancelled or past visits.

### 20. 1-hour booking cutoff replaces the simple past-date check
**Decision:** `validate_slot` now rejects any booking less than 1 hour from the current time, rather than just rejecting bookings already in the past.
**Reasoning:** The stricter check makes the old one redundant (anything in the past is automatically more than 1 hour away from "now" in the wrong direction), so it replaces rather than supplements the original check. Matches the assessment's bonus requirement directly.

### 21. Dependency management: `pip freeze` to catch missing packages
**Decision:** After a Render deploy crashed with `Exited with status 128`, I regenerated `requirements.txt` using `pip freeze` instead of trying to manually track every package I'd installed.
**Reasoning:** I'd installed `psycopg2` locally at some point without adding it to `requirements.txt` by hand, so it worked on my machine but wasn't available in the clean Docker container Render builds from. `pip freeze` captures everything actually installed in my environment, which is more reliable than remembering to update the file manually every time I add a dependency.

---

*This log was kept current throughout the build — from initial system design through deployment and testing.*