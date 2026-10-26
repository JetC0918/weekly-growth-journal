# Render deployment

`render.yaml` defines a full-stack Render deployment for the TanStack Start
frontend and Django API. Both use the repository's Dockerfiles and deploy only
after GitHub CI passes. This is a free-tier hobby setup, not a production
availability guarantee.

## Database and environment

The API uses a PostgreSQL database outside Render. Set `DATABASE_URL` when
Render prompts for the Blueprint's unsynchronized secret. Use the Neon free
PostgreSQL connection string with TLS (`sslmode=require`). This project uses
PostgreSQL transactions and row locking; do not substitute SQLite or D1.

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
3. Supply the Neon `DATABASE_URL` when prompted. Do not paste it into the
   repository or a build-time frontend variable.
4. Create the API and frontend services. Render deploys both Docker images after
   the configured GitHub checks pass.
5. Wait for each service's first deploy and database migration to finish. Test
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
- Render Free Postgres expires 30 days after creation, so this Blueprint leaves
  the database external. Neon Free currently provides 1 GB of storage and 100
  compute hours per project monthly; its database can also sleep while idle.
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
[Neon free-plan limits](https://github.com/neondatabase/website/blob/main/content/faqs/free-plan-limits.md).
