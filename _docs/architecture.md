# System architecture

**Status:** Current repository architecture, with planned deployment work labeled separately.

This describes source inspected on 2026-10-26, including the current working-tree Cloudflare proof-of-concept files; some deployment files are untracked in this workspace. The application implements frontend-to-Django HTTP integration and PostgreSQL-backed journal models. It retains a mock service and an earlier FastAPI prototype. Cloudflare configuration and a gated deployment workflow now exist in the working tree, but no live deployment or Cloudflare runtime verification has been reported.

## Implemented components

| Area | Current implementation | Evidence |
| --- | --- | --- |
| Frontend | TanStack Start, React 19, and TypeScript app, managed with Bun. Vite serves local development; TanStack Query caches service results. Journal routes disable SSR and require a session. | [`frontend/package.json`](../frontend/package.json), [`frontend/vite.config.ts`](../frontend/vite.config.ts), [`frontend/src/services/index.ts`](../frontend/src/services/index.ts), [`frontend/src/services/queries.ts`](../frontend/src/services/queries.ts), [`frontend/src/routes/review.tsx`](../frontend/src/routes/review.tsx) |
| HTTP boundary | The app wires `createHttpService` as its active `GrowthService`. It sends JSON to `VITE_API_BASE_URL` (default `/api`), attaches a bearer token, and translates failed requests to `ApiError`. | [`frontend/src/services/api.ts`](../frontend/src/services/api.ts), [`frontend/src/services/httpService.ts`](../frontend/src/services/httpService.ts) |
| Browser session | Registration/login keep the access token in module memory for up to 24 hours; reloading starts signed out. Expiry or an API 401 clears the session. Identity/session changes clear the query cache; sign-out redirects to the account screen. | [`frontend/src/services/auth.ts`](../frontend/src/services/auth.ts), [`frontend/src/lib/session-cache.ts`](../frontend/src/lib/session-cache.ts), [`frontend/src/routes/__root.tsx`](../frontend/src/routes/__root.tsx) |
| API | Django 5 and Django REST Framework provide account registration/login, health, journal, report, commitment, and data-deletion endpoints. Protected endpoints use signed bearer authentication and default to authenticated access. | [`backend/config/urls.py`](../backend/config/urls.py), [`backend/journal/urls.py`](../backend/journal/urls.py), [`backend/accounts/authentication.py`](../backend/accounts/authentication.py), [`backend/config/settings.py`](../backend/config/settings.py) |
| Persistence | PostgreSQL stores Django accounts and journal records. Reviews have a unique user/week constraint; deleting a review cascades to its report and commitment. Compose gives PostgreSQL a persistent volume and health check. | [`backend/journal/models.py`](../backend/journal/models.py), [`backend/journal/migrations/0001_initial.py`](../backend/journal/migrations/0001_initial.py), [`docker-compose.yml`](../docker-compose.yml) |
| Feedback generation | A backend provider interface supports deterministic fake output and an optional OpenAI-compatible provider. It is used for follow-up questions and reports. Reports are shape-checked, evidence must occur in supplied reflection text, and report persistence plus review completion use a database transaction. | [`backend/feedback/follow_ups.py`](../backend/feedback/follow_ups.py), [`backend/feedback/reports.py`](../backend/feedback/reports.py), [`backend/journal/views.py`](../backend/journal/views.py) |

The checked-in [`openapi.yaml`](../openapi.yaml) describes the intended HTTP contract. The frontend service and Django URL/view/serializer code are the implementation; the contract alone does not establish that every documented behavior is implemented or deployed. For example, absent individual resources are returned as JSON `null` in several Django views, while deletes return `204`.

The contract's introductory claim that the frontend uses a local mock and its FastAPI validation wording are legacy prose. Django deliberately retains the documented `422` validation-detail array for account requests through [`accounts/exceptions.py`](../backend/accounts/exceptions.py); journal validation returns `400` with a detail string. The HTTP client tests use explicit request expectations and mocked responses, not an automatic OpenAPI conformance validator.

## Request and data flow

1. The browser calls the shared `GrowthService`; route components do not own API transport.
2. The HTTP service sends the request to Django and adds `Authorization: Bearer …` when a session token is in memory.
3. Django authenticates the token, validates request data, and scopes journal queries to the current user.
4. Django reads and writes PostgreSQL models. Review completion obtains up to five earlier completed reviews from that user and calls the provider before opening the write transaction. After validating the result, it locks the review, preserves user-edited insights, and saves the report and completed state atomically. Provider/validation failures leave the prior state unchanged; database failures roll back persistence.
5. The frontend renders reports and sends insight edits or commitment updates through the same HTTP boundary.

Local setup and commands are in [`README.md`](../README.md) and [`backend/README.md`](../backend/README.md). The current working-tree [`docker-compose.yml`](../docker-compose.yml) defines a full local stack, started with `docker compose up --build`:

- PostgreSQL 16 exposes host port 5433 and retains data in a named volume.
- The [`backend/Dockerfile`](../backend/Dockerfile) installs locked Python dependencies, runs migrations, then serves Django's ASGI application with Uvicorn on port 8000. It waits for the database health check.
- The [`frontend/Dockerfile`](../frontend/Dockerfile) builds with Bun and `NITRO_PRESET=node-server`, then serves the generated output with Node on port 3000. Its public `VITE_API_BASE_URL` is compiled at build time, defaulting to `http://localhost:8000/api` for the browser. Compose waits for backend health before starting it and configures local CORS for `http://localhost:3000`.

These are local container definitions, not evidence of a successful image build, running stack, or Cloudflare deployment. For direct development, start only `db` with Compose, run Django with root [`manage.py`](../manage.py) (a shim) or [`backend/manage.py`](../backend/manage.py), and run Vite separately. Vite's `/api` development proxy forwards to Django on port 8000. The unauthenticated [`/api/health/` view](../backend/config/views.py) returns a static status; it is not a database readiness check.

## Data and security boundaries

`Review`, `FeedbackReport`, and `Commitment` are Django models in [`backend/journal/models.py`](../backend/journal/models.py). A review belongs to an account and has JSON answers/follow-ups/previous-action data, free writing, a week date, and draft/completed status. The frontend chooses Mondays; the current backend serializer validates a date without enforcing Monday. A report and commitment are each one-to-one with a review. Journal records use UUID database keys exposed with `rev_`, `rep_`, and `com_` prefixes, and timestamps use Django's UTC configuration. The unique user/week constraint and descending user/week index support lookup and history.

The journal views scope access to the authenticated account. Deleting a review cascades to its report and commitment; `DELETE /api/data` deletes only that user's journal data and preserves the account. The prior-commitment lookup chooses the most recent week strictly before the requested date. Django accounts use password hashing, while [`accounts/tokens.py`](../backend/accounts/tokens.py) implements custom HMAC-SHA256 signed bearer tokens with a 24-hour expiry. There is no refresh-token endpoint; browser sign-out discards its token.

`DATABASE_URL` or `POSTGRES_*` settings configure PostgreSQL. Django's bearer-token signing, CORS, allowed-host, debug, and provider settings are read from environment variables; safe local defaults are documented in [`.env.example`](../.env.example). Production CORS requires exact configured HTTPS origins and disables cookie credentials. These settings and deployment checks prepare the application for deployment; they do not provision hosting or secure a deployed instance.

AI provider behavior depends on configuration. The repository example and local Compose defaults select `AI_PROVIDER_MODE=fake`, `DJANGO_DEBUG=true`, and a blank `AI_API_KEY` for deterministic behavior. The Django settings themselves default provider mode to `openai`, but the provider makes no external request until its URL, model, and API key are configured. Fake mode is restricted to debug use. See [`backend/README.md`](../backend/README.md) and [`backend/config/checks.py`](../backend/config/checks.py). No provider call or external AI service is implied by the presence of the adapter.

## Tests and contracts

Test files are present; their presence does not show that they were run or passed. The repository includes:

- Frontend Vitest/jsdom tests cover [HTTP request mapping and errors](../frontend/src/services/httpService.test.ts), [active HTTP wiring](../frontend/src/test/service-wiring.test.ts), mock service behavior, week/date rules, account flows, routing, session cache, and journal edit/delete flows. They use mocks rather than a live browser-to-Django stack.
- Django tests cover [accounts and health](../backend/accounts/tests.py), [configuration/CORS](../backend/config/tests.py), [journal persistence, isolation, deletion, and a deterministic two-week journey](../backend/journal/tests.py), and [provider validation/failure/rollback behavior](../backend/feedback/tests.py). Database tests use Django's PostgreSQL test database; provider tests inject fakes or mock transport. The two-week journey uses an API client, not a browser.
- Pytest [API compatibility](../backend/tests/test_api.py) and [OpenAPI smoke](../backend/tests/test_smoke.py) tests exercise only the transitional FastAPI app with its process-local store. Django health coverage belongs to the Django suite.

Commands and database prerequisites are listed in [`AGENTS.md`](../AGENTS.md) and [`README.md`](../README.md). No test result is claimed here; check the task's workflow record for verification performed on a particular change.

The current working tree contains a [CI workflow](../.github/workflows/ci.yml) for Django unit and PostgreSQL integration tests, frontend tests/lint/build, and Compose configuration and container builds. It does not run dependency advisory scans. The [Cloudflare deployment workflow](../.github/workflows/deploy-cloudflare.yml) is gated on successful CI for `main`, the repository variable `CLOUDFLARE_DEPLOY_ENABLED=true`, and required GitHub secrets and variables; it deploys the API and frontend Workers, then checks the public API health endpoint and frontend root. These are configured steps, not evidence that CI or deployment ran. No full deployed journal journey is configured or reported. A green CI run proves only the checks reported for that revision.

### Reported QA results

The following results were supplied in a QA update on 2026-10-26 and were not rerun during this documentation change:

- `uv run python backend/manage.py test backend.config` — 20 tests passed, including PostgreSQL SSL mode behavior.
- Frontend lint — 0 errors and 7 existing `react-refresh` warnings.
- Earlier shared QA notes report that the full-app Compose run and Django unit/integration and frontend tests passed. Those notes did not include the run IDs, exact revisions, commands, or result counts, so they are attributed reports rather than independently traceable results here.

The newer QA update supplied no run URL/ID, exact revision, or test environment; it also did not name the frontend lint command. These are attributed reports, not verification performed for this documentation update.

These reports do not establish Cloudflare compatibility or a live deployment. See the dated evidence in [`ai-development-workflow.md`](ai-development-workflow.md).

## Transitional code and planned deployment

The active frontend uses the HTTP service. [`frontend/src/services/mock/`](../frontend/src/services/mock/) retains heuristic feedback generation and an injectable key/value store that defaults to memory; it is exercised by mock-service tests, not selected by the app-wide service export. The earlier FastAPI app under [`backend/app/`](../backend/app/) uses a seeded process-local store. It is transitional, and FastAPI/Uvicorn dependencies remain in [`pyproject.toml`](../pyproject.toml). Django under `backend/config/` is the documented API launch path and uses PostgreSQL; the legacy store is not its persistence layer.

Cloudflare Workers for the frontend/API and a managed PostgreSQL connection through Hyperdrive are a **configured proof of concept, still unverified at runtime**. The current working tree contains a frontend Wrangler config, an isolated Python Worker adapter and Hyperdrive binding, and the conditional deployment workflow. The workflow requires successful CI on `main`, `CLOUDFLARE_DEPLOY_ENABLED=true`, and account-specific secrets/variables before deployment. It performs HTTP checks of the API health route and frontend root after deployment. No Cloudflare account credentials were available or used for this work; the workflow has not run and no live Worker, managed database, deployed smoke check, or real journal journey is verified. Python Worker package/driver compatibility, PostgreSQL transactions and locking, and Hyperdrive TLS behavior remain proof-of-concept gates. See the [CI/CD and Cloudflare deployment status](cicd.md) for configuration requirements and release checks.

The deployment notes in [`private-deployment.md`](private-deployment.md) describe private access, production configuration, and backup/restore preparation. Remaining work includes verifying Python Worker/package and PostgreSQL driver compatibility, configuring the deployment and Hyperdrive binding, validating current platform limits, provisioning access/secrets/backups, and recording staged smoke and restore checks. Production CORS checks exist locally; deployed origin/preflight behavior remains unverified. No quota estimate, successful release, managed database, or deployed environment is asserted here.

## Observability

When `OTEL_EXPORTER_OTLP_ENDPOINT` is configured, Django exports request traces, HTTP request metrics, and privacy-safe workflow logs over OTLP. Resource attributes identify the service, environment, and `APP_VERSION`. Successful account and journal milestones plus safe failure outcomes increment the low-cardinality `journal.workflow.events` counter. Report generation has an explicit span. Raw URL paths and query strings are replaced before server spans are exported; telemetry excludes user IDs, usernames, review text, prompts, provider payloads, access tokens, and authorization headers.

The separate [`observability/`](../observability/) Compose project contains the OpenTelemetry Collector, Prometheus, Loki, Tempo, and Grafana. Its provisioned dashboard shows weekly workflow events, request latency, correlated logs, and traces, filterable by environment and version. This is a local telemetry UI artifact; no remote collector or deployed dashboard is configured. Start the application Compose project first so it creates the shared telemetry network, then start the observability project. See [`observability.md`](observability.md) for exact steps and the privacy boundary.
