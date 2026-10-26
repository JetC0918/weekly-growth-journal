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

The repository contains a TanStack Start frontend and a Django/DRF backend. The frontend's `GrowthService` calls the Django API. Django uses PostgreSQL for account and journal data, with optional OpenAI-compatible report and follow-up generation that stays inactive when `AI_API_KEY` is blank. See [`_docs/architecture.md`](_docs/architecture.md) for current component boundaries and deployment configuration.

The product direction and broader MVP scope are documented in [`_docs/specs.md`](_docs/specs.md). The Render Blueprint deploys the frontend and Django API as Docker services and provisions a Render PostgreSQL database; deployment steps and free-tier limits are in [`_docs/render-deployment.md`](_docs/render-deployment.md). The free database expires after 30 days and is deleted after a further 14-day grace period unless upgraded, so it is not durable storage for personal data. Production CORS requires explicit HTTPS frontend origins and is enforced by Django's CORS middleware.

The local OpenTelemetry stack and Grafana dashboard are described in [`_docs/observability.md`](_docs/observability.md). The latest security review, retained scan evidence, and audit limitations are in [`_docs/security-audit/run-4/REPORT.md`](_docs/security-audit/run-4/REPORT.md).

CI checks, separate Django/PostgreSQL integration coverage, and deployment
automation are described in [`_docs/cicd.md`](_docs/cicd.md).

## Live demo

- **Frontend:** [weekly-growth-journal-frontend.onrender.com](https://weekly-growth-journal-frontend.onrender.com/)
- **API health:** [weekly-growth-journal-api.onrender.com/api/health/](https://weekly-growth-journal-api.onrender.com/api/health/)

The frontend opens at account access. Choose **Explore the demo account** to
open a browser-local sample account with three past weekly reviews, sample
feedback reports, and commitments. Demo data is separate from production
accounts; edits are saved only in that browser and can be erased from History.
You can also create your own account and use synthetic, non-sensitive entries.
The API health endpoint
currently reports HTTP availability; it does not verify database readiness or
prove a complete account-to-journal workflow. See the [Render deployment
guide](_docs/render-deployment.md) for deployment details and free-tier limits.

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
isolation, draft/report/insight/commitment behavior, and data deletion.

See [`backend/README.md`](backend/README.md) for database configuration.

## Project layout

- `frontend/` — TanStack Start, React, and TypeScript app, including its mock service and frontend tests.
- `backend/` — Django/DRF API and Docker image definition.
- `docker-compose.yml` — PostgreSQL, Django API, and production-built frontend for local full-stack use.
- `observability/` — separate local OpenTelemetry Collector, Prometheus, Loki, Tempo, and Grafana stack.
- `.github/workflows/ci.yml` — pull-request/main backend, frontend, container, dependency-audit, and tracked-content guardrail checks.
- `render.yaml` — Render Blueprint for the frontend, API, and PostgreSQL database.
- `openapi.yaml` — API contract for the backend.
- `_docs/specs.md` — product problem, MVP decisions, expected experience, scope, and success criteria.
- `_docs/process.md` — project work process and role responsibilities.
- `_docs/team/` — PM, engineer, and QA role instructions.
- `agent-capabilities/`, `agent-hooks/`, `mcp-server/`, `plugins/`, and `docs/agent-extension-pack.md` — reusable local-first agent extension pack and its permission/data policies.

## Rubric evidence map

The project rubric is a draft. This map points reviewers to implementation and
verification evidence and calls out checks that still need a real review or
runtime result. A configured workflow or dashboard is not evidence that it ran.

| Rubric area | Max points | Evidence and current limit |
| --- | ---: | --- |
| Problem description | 2 | The [problem](#the-problem) and [expected behavior](#expected-behavior) sections describe the user need and product flow; broader scope is in [`_docs/specs.md`](_docs/specs.md). |
| AI-assisted development workflow | 2 | [`_docs/ai-development-workflow.md`](_docs/ai-development-workflow.md) records context, task summaries, handoffs, AI review, and verification. **Human review is not yet recorded**; add reviewer, date, decision, and any requested changes after review. |
| Technologies and architecture | 2 | [`_docs/architecture.md`](_docs/architecture.md) describes the frontend, Django API, PostgreSQL, containers, CI, and deployment setup. |
| Frontend | 3 | `frontend/` contains the TanStack Start app, centralized `GrowthService` transport, and tests. Run frontend tests with `cd frontend && bun run test`; run `bun run lint` for linting. |
| API contract | 2 | [`openapi.yaml`](openapi.yaml) describes the HTTP contract; Django routes, serializers, and frontend service implement it. |
| Backend | 3 | `backend/` contains the Django/DRF API and tests for authentication, health, journal ownership, persistence, and provider behavior. See [`backend/README.md`](backend/README.md). |
| Database integration | 2 | Django models and migrations persist account-owned journal data in PostgreSQL; configuration is documented in [`backend/README.md`](backend/README.md). |
| Containerization | 2 | [`docker-compose.yml`](docker-compose.yml) runs PostgreSQL, the API, and frontend together; see [Run the full app with Docker](#run-the-full-app-with-docker). |
| Integration testing | 2 | Django integration tests use the `integration` tag and a PostgreSQL test database. The separate commands are in [Run services directly](#run-services-directly). |
| Deployment | 2 | The [live frontend](https://weekly-growth-journal-frontend.onrender.com/) and [API health endpoint](https://weekly-growth-journal-api.onrender.com/api/health/) are available on Render. A full authenticated journal journey and database-backed smoke test still need to be recorded. |
| CI/CD | 2 | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) defines test, build, and audit jobs. [`render.yaml`](render.yaml) configures Render deployment after checks pass. Link or record a successful run for the exact revision being reviewed. |
| Agent extension pack | 2 | [`docs/agent-extension-pack.md`](docs/agent-extension-pack.md) indexes the reusable capability, specialist, MCP server, hook, permission notes, and AI data policy. |
| Security, audit, and DevOps hardening | 2 | [`_docs/security-audit/run-4/REPORT.md`](_docs/security-audit/run-4/REPORT.md) and its `evidence/` directory contain the latest audit evidence and limits. Extension boundaries are in [`docs/permissions.md`](docs/permissions.md); AI data handling is in [`docs/ai-tool-data-policy.md`](docs/ai-tool-data-policy.md). |
| Reproducibility | 2 | Setup, run, test, and deployment instructions are in this README, [`AGENTS.md`](AGENTS.md), [`backend/README.md`](backend/README.md), and [`_docs/render-deployment.md`](_docs/render-deployment.md). |
| Observability | 2 | [`_docs/observability.md`](_docs/observability.md) describes OpenTelemetry and the Grafana/Prometheus/Loki/Tempo stack. **A correlated journey in Grafana is not yet recorded.** |
| Alerting on user impact | 1 | **Not configured yet.** Add and demonstrate an alert for a user-facing failure or elevated error/latency signal. |
| On-call agent | 2 | **Not implemented yet.** There is no alert-triggered agent diagnosis and verified fix recorded. |

## Development workflow

The project uses AI coding assistance with repository instructions and a documented PM/engineer/QA workflow. See [`_docs/ai-development-workflow.md`](_docs/ai-development-workflow.md) for the evidence record format and currently recorded evidence, and [`AGENTS.md`](AGENTS.md) and [`_docs/process.md`](_docs/process.md) for project instructions.
