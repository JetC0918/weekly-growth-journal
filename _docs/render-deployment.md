# Render deployment

`render.yaml` defines a full-stack Render deployment for the TanStack Start
frontend and Django API. Both use the repository's Dockerfiles and deploy only
after GitHub CI passes. This is a free-tier hobby setup, not a production
availability guarantee.

## Database and environment

The Blueprint creates a Render PostgreSQL database in Singapore and supplies
its internal connection string to the API as `DATABASE_URL`. Production Django
configuration requires TLS for this connection. This project uses PostgreSQL
transactions and row locking; do not substitute SQLite.

The Blueprint generates separate `DJANGO_SECRET_KEY` and `TOKEN_SIGNING_KEY`
values. Keep `AI_API_KEY` blank unless you deliberately enable the external AI
provider. The Django production check requires PostgreSQL, TLS, explicit hosts,
HTTPS CORS, and distinct signing keys.

The service names determine the expected default Render origins:

- Frontend: `https://weekly-growth-journal-frontend.onrender.com`
- API: `https://weekly-growth-journal-api.onrender.com`

If Render assigns different hostnames, update `DJANGO_ALLOWED_HOSTS`,
`CORS_ALLOWED_ORIGINS`, and the frontend `VITE_API_BASE_URL` in the Blueprint
and sync it again. `VITE_API_BASE_URL` is compiled into the frontend image.

## Create the Render services

1. Push the repository to GitHub and connect it to Render.
2. In Render, create a Blueprint from the repository and select `render.yaml`.
3. Create the Blueprint resources. Render provisions the database and injects
   its internal URL into the API service; no external database URL is needed.
4. Wait for the API and frontend Docker services to deploy after the configured
   GitHub checks pass, and for the API's startup migration to finish. Test
   `/api/health/`, then perform a synthetic account registration/login and a
   review save/read/delete journey before using personal data.

The API container applies migrations at startup. Render's `/api/health/` check
only verifies HTTP availability; it does not check database readiness or prove
the journal flow works.

## Free-tier constraints

- Render Free web services sleep after 15 minutes without inbound traffic. A
  sleeping service can take about a minute to wake.
- Free service storage is ephemeral. Journal data belongs in PostgreSQL, never
  in the container filesystem.
- Render Free Postgres provides 1 GB and expires 30 days after creation. After
  expiration, the database is inaccessible; there is a 14-day upgrade grace
  period before Render deletes it and its data. Upgrade before the deadline or
  export and restore the data elsewhere. Free Postgres has no backups, so do not
  treat it as durable storage for personal journal data.
- Render may suspend a free service that initiates unusually high external
  traffic. Keep database and provider traffic modest and watch workspace usage.
- Free plans are intended for hobby projects and previews, not a dependable
  production service. Keep encrypted backups of journal data.

## Verification and release evidence

Record the deployed commit, Blueprint/service URLs, database migration result,
health result, synthetic user journey, and rollback outcome. Never put journal
content, credentials, tokens, or provider payloads in logs or evidence records.
No live Render deployment is claimed until the steps above have been completed.

References: [Render Blueprints](https://render.com/docs/blueprint-spec),
[Render free services](https://render.com/docs/free), and
[connecting to Render Postgres](https://render.com/docs/postgresql-creating-connecting).
