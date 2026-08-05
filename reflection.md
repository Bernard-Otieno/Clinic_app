# Section 4 — AI Reflection

## 1. What did you use AI for across the four sections?

- Planning the steps needed to achieve the project's goals — for example, in Section 1, I used AI to help choose which platforms to use for hosting and the database, and to design the data model.
- Debugging errors — for example, using AI to track down a missing dependency (`psycopg2`) that was causing SQLAlchemy installation/runtime failures.
- Generating a brief checklist of all requirements across the four sections, so I had something quick to reference instead of constantly re-reading the original assessment document.
- Drafting the README file and making sure it covered everything the assessment asked for.
- Working through logical issues in the booking logic together.

## 2. Give one example where an AI suggestion improved your work. What did you prompt it with?

**File and folder arrangement.** I hadn't thought deeply about how to structure the project into folders. AI suggested not just the structure but a naming scheme that makes it obvious where to find things — for example, when I needed a frontend, it named the folder `static`, a common term in frontend development, which immediately signals that anything to do with the API logic won't be found there.

## 3. Give one example where AI output was wrong or incomplete and how you caught it.

The Render server was crashing due to a missing dependency, `psycopg2`. It wasn't listed in `requirements.txt`, and after running `pip freeze`, it was correctly captured and saved.

Separately, our `Dockerfile` specifies a `python:3.10-slim` base image. This combination caused an installation error for `psycopg2-binary` on the build server that didn't show up on my own machine, since my local environment already had the right build tools present. This was caught by comparing the working local setup against the failing deployed one and identifying the missing piece in the containerized environment specifically.

## 4. Name two decisions you made without AI. Why did you trust your own judgment there?

- **Using GitHub Actions for CI/CD.** This simplified the overall workflow — having one platform perform the necessary checks and tests, right next to the code, makes it easier to track what's actually been accomplished and verified.
- **Keeping the frontend deliberately lightweight**, just enough to visualize the booking system. Related to this, I chose UUIDs over sequential IDs specifically because sequential IDs are guessable and can leak information — if a patient's appointment is `/appointments/47`, someone could simply try `/appointments/48`, `/appointments/49`, and so on.

The reasoning behind both came from experience with similar systems I've built before: UUIDs help prevent people from accessing information they shouldn't be able to, and keeping most of the workflow on one platform keeps things simple to reason about and maintain.