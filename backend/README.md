# Django backend

The documented backend is Django with Django REST Framework. It provides
authenticated account and journal APIs backed by PostgreSQL, including an
OpenAI-compatible adapter for optional follow-up questions. The adapter makes
no provider request while its configuration is incomplete; the checked-in
configuration leaves `AI_API_KEY` blank.

The FastAPI code under `backend/app/` is a transitional prototype. It is not the
documented backend launch path and does not provide the Django persistence
architecture.

## Local setup

Run these commands from the repository root:

```sh
uv sync
docker compose up -d db
uv run python backend/manage.py migrate
uv run python backend/manage.py runserver 0.0.0.0:8000
```

The Compose service starts PostgreSQL on host port `5433` and keeps its data in
the `postgres_data` volume. The nonstandard host port avoids collisions with
another local PostgreSQL server. Stop the database with `docker compose down`;
this preserves that volume.

The settings read either `DATABASE_URL` or the individual `POSTGRES_DB`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`
environment variables. Local defaults match the Compose database. Set
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and `DJANGO_ALLOWED_HOSTS` through the
environment when changing the local security configuration; never reuse the
development secret in a deployed environment.

`APP_ENV` defaults to `development`. For production, set `APP_ENV=production`,
disable `DJANGO_DEBUG`, provide separate production `DJANGO_SECRET_KEY` and
`TOKEN_SIGNING_KEY` values, configure a PostgreSQL connection, and set an
explicit non-wildcard `DJANGO_ALLOWED_HOSTS` list. Run
`uv run python backend/manage.py check --deploy` with production settings
loaded from the private secret manager. Set `CORS_ALLOWED_ORIGINS` to exact
HTTPS frontend origins, comma-separated and without paths or trailing slashes;
the deployment check rejects missing, wildcard, non-HTTPS, and malformed
origins. CORS allows only `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS` with
`Authorization` and `Content-Type`; cookie credentials are disabled. Local Vite
proxy development needs no allowlist. AI provider settings are optional and do
not prevent startup when `AI_API_KEY` is blank. See
[`_docs/private-deployment.md`](../_docs/private-deployment.md) for private
access and backup/restore preparation.

## Optional follow-up question provider

For a local browser walkthrough with no provider credentials, set
`AI_PROVIDER_MODE=fake` while `DJANGO_DEBUG=true`. This mode returns predictable
follow-up questions and a deterministic report whose evidence is copied from
the supplied review/history. It is available only with debug enabled; if
`DEBUG` is false, both API provider factories fail safely, and production
deployment checks reject fake mode. The checked-in `.env.example` selects this
local mode and keeps `AI_API_KEY` blank.

Set `AI_PROVIDER_MODE=openai` to use the optional live provider. This mode still
makes no request unless its base URL, model, and API key are all configured.

`POST /api/reviews/suggest-follow-ups` returns `200 []` when the submitted
answers, free writing, and follow-up answers are blank. For a non-empty draft,
the backend sends the reflection to an OpenAI-compatible Chat Completions API
only when all three server-side settings are configured:

- `AI_BASE_URL` — API base URL, such as `https://api.openai.com/v1`.
- `AI_MODEL` — model name accepted by that provider.
- `AI_API_KEY` — server-side bearer credential.

The safe example values are in [`.env.example`](../.env.example). Keep the
checked-in key blank. With `AI_API_KEY` unset, non-empty follow-up requests
return `503` with a setup message and make no network call. Provider timeouts,
connection or HTTP failures, and unusable output return a safe `502`. The API
key is not configured in this local environment; no provider calls are made by
default. `POST /api/reviews/{reviewId}/complete` uses the same optional provider
to generate a structured report. A review without any non-blank answer,
free-writing entry, or follow-up answer returns `422` without a provider request.
Provider or output validation failures return a safe `502`, and incomplete
configuration returns `503`; these failures leave the review and any previous
report unchanged. On success, the report is validated and persisted with the
review's completed status in one database transaction. The provider receives
the current reflection and up to five most recent earlier completed reviews
belonging to the same user.

## Check and test

From the repository root:

```sh
uv run python backend/manage.py check
uv run python backend/manage.py test
```

`GET /api/health/` returns `{"status":"ok"}` without authentication. Account
and journal endpoints require the documented bearer token.

The older FastAPI tests can still be run separately with `uv sync --extra test`
and `uv run pytest` from the repository root. They exercise transitional code,
not the Django API.
