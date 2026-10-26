# Weekly Growth Journal

Weekly Growth Journal is a private, personal reflection tool. It helps someone turn a short review of their week into a practical improvement commitment, then check in on that commitment during the next review.

## The problem

A journal can capture what happened without helping someone notice repeated patterns or decide what to change. Weekly Growth Journal is designed to close that gap with a simple feedback loop: reflect, review grounded feedback, choose one action, and revisit it the following week.

The initial audience is one person using the app for personal growth across habits, work, communication, thinking, and self-defined goals. Team feedback, public sharing, daily check-ins, and complex scoring are outside the initial scope.

## Expected behavior

For each week, a user should be able to:

1. Answer five short prompts about what went well, what did not, what they could handle differently, what they learned, and what they want to change next week.
2. Add free-form notes and optionally answer follow-up questions based on their reflection.
3. Save a draft or complete the review to receive a feedback report.
4. Review takeaways, strengths, challenges, and possible recurring patterns, with observations distinguished from hypotheses and linked to the user's own words.
5. Accept, reject, or correct feedback, then set one primary commitment for the coming week.
6. Browse past reviews and report on the previous commitment during the next weekly reflection.
7. Edit or delete their reflection data.

The product aims to help users reflect consistently, find feedback useful, and follow through on a small action. These are product hypotheses, not validated results.

## Current implementation

The repository contains a TanStack Start frontend and a Django/DRF backend. The frontend's `GrowthService` calls the Django API. Django uses PostgreSQL for account and journal data, with optional OpenAI-compatible report and follow-up generation that stays inactive when `AI_API_KEY` is blank. The earlier FastAPI implementation under `backend/app/` is transitional and is not the backend launch path. See [`_docs/architecture.md`](_docs/architecture.md) for current component boundaries and planned deployment status.

The product direction and broader MVP scope are documented in [`_docs/specs.md`](_docs/specs.md). The private deployment preparation, production configuration checks, CORS allowlist requirements, and PostgreSQL backup/restore guidance are in [`_docs/private-deployment.md`](_docs/private-deployment.md). Production CORS requires explicit HTTPS frontend origins and is enforced by Django's CORS middleware.

## Run locally

### Run the full app with Docker

You need Docker Desktop or Docker Engine with Compose. From the repository root:

```sh
docker compose up --build
```

Compose starts PostgreSQL, runs Django migrations and the API, then starts the
production-built frontend. Open `http://localhost:3000`; the API health endpoint
is `http://localhost:8000/api/health/`. Local defaults use deterministic fake
feedback and do not call an AI provider. Set `AI_PROVIDER_MODE=openai` and
`AI_API_KEY` in a local `.env` file to opt into a configured provider. PostgreSQL
data persists in the `postgres_data` volume. Stop the services with
`docker compose down`; add `-v` only when you intend to delete that database.

Override the local ports with `FRONTEND_PORT`, `BACKEND_PORT`, and
`POSTGRES_PORT` in `.env` if needed. If the frontend or backend port changes,
also set `CORS_ALLOWED_ORIGINS` and `VITE_API_BASE_URL` to the matching browser
origins, then rebuild the frontend image. `VITE_API_BASE_URL` is compiled into
that image; its default is `http://localhost:8000/api`.

### Run services directly

For frontend-only development outside containers, you need [Bun](https://bun.sh/)
installed.

```sh
cd frontend
bun install --frozen-lockfile
bun run dev
```

Open the local URL printed by Vite. To run the frontend tests or lint check:

```sh
cd frontend
bun run test
bun run lint
```

To run the Django API locally, start PostgreSQL and apply Django's built-in migrations:

```sh
uv sync
docker compose up -d db
uv run python backend/manage.py migrate
uv run python backend/manage.py runserver 0.0.0.0:8000
```

The unauthenticated health endpoint is `http://localhost:8000/api/health/` and
returns `{"status":"ok"}`. With dependencies installed and PostgreSQL running
as described above, run the Django test groups from the repository root:

Run non-integration Django checks and endpoint integration tests separately, or
run the complete Django suite:

```sh
uv run python backend/manage.py check
uv run python backend/manage.py test --exclude-tag=integration
uv run python backend/manage.py test --tag=integration
uv run python backend/manage.py test
```

The integration group uses Django's isolated PostgreSQL test database and
deterministic provider fakes. It covers authenticated endpoint flows, user
isolation, draft/report/insight/commitment behavior, and data deletion. The
separate compatibility suite checks only the transitional FastAPI prototype
and in-memory store; it is not Django integration coverage. Run it from the
repository root with:

```sh
uv sync --extra test
uv run pytest
```

See [`backend/README.md`](backend/README.md) for database configuration and the
transition note.

## Project layout

- `frontend/` — TanStack Start, React, and TypeScript app, including its mock service and frontend tests.
- `backend/` — Django/DRF API, Docker image definition, and transitional FastAPI source under `backend/app/`.
- `docker-compose.yml` — PostgreSQL, Django API, and production-built frontend for local full-stack use.
- `openapi.yaml` — API contract for the backend.
- `_docs/specs.md` — product problem, MVP decisions, expected experience, scope, and success criteria.
- `_docs/process.md` — project work process and role responsibilities.
- `_docs/team/` — PM, engineer, and QA role instructions.

## Development workflow

The project uses AI coding assistance with repository instructions and a documented PM/engineer/QA workflow. See [`_docs/ai-development-workflow.md`](_docs/ai-development-workflow.md) for the evidence record format and currently recorded evidence, and [`AGENTS.md`](AGENTS.md) and [`_docs/process.md`](_docs/process.md) for project instructions.
