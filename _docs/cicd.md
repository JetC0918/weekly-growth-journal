# CI and Cloudflare deployment

## Continuous integration

The `CI` workflow runs for pushes and pull requests. The production deployment
workflow listens for a completed `CI` run and proceeds only when the checked
commit is on `main` and CI succeeded.

## Cloudflare deployment status

This repository contains a conditional deployment proof of concept. It has not
been deployed to a Cloudflare account, and no Cloudflare resource IDs or account
credentials are committed. The deployment job stays skipped until the
repository variable `CLOUDFLARE_DEPLOY_ENABLED` is set to `true`.

Cloudflare currently documents Django adapters for Python Workers and
PostgreSQL access through Hyperdrive. The Worker project is isolated under
`backend/cloudflare/`; its `workers-py` tooling is not part of the main project
dependencies and has its own `uv.lock` for reproducible deployment installs. The existing frontend build wrapper defaults to a Cloudflare
Nitro target, while the regular Docker build continues to select its existing
Node server target.

## Staging deployment

The `Deploy to Cloudflare staging` workflow is a manual release to isolated
Workers. In GitHub Actions, select the workflow, choose `main`, check the
confirmation input, and run it. It deploys `weekly-growth-journal-api-staging`
and `weekly-growth-journal-frontend-staging` using the `cloudflare-staging`
GitHub Environment. It never runs database migrations; apply and verify them
against the staging database from a trusted environment before deploying.

Configure the `cloudflare-staging` Environment with these variables:

- `CLOUDFLARE_HYPERDRIVE_ID`: the staging Supabase Hyperdrive ID.
- `CLOUDFLARE_API_ORIGIN`: exact HTTPS origin for the staging API Worker.
- `CLOUDFLARE_FRONTEND_ORIGIN`: exact HTTPS origin for the staging frontend Worker.

Configure these environment secrets: `CLOUDFLARE_API_TOKEN`,
`CLOUDFLARE_ACCOUNT_ID`, `CF_DJANGO_SECRET_KEY`, `CF_TOKEN_SIGNING_KEY`,
`CF_DJANGO_ALLOWED_HOSTS`, and `CF_CORS_ALLOWED_ORIGINS`. Use staging-only
signing keys. The allowed-host value must include the API hostname without a
scheme; the CORS value must exactly equal the frontend origin. Keep the
production environment and deployment switch separate.

## Required GitHub configuration

Add these GitHub Actions **secrets**:

| Name | Value |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | A narrowly scoped Cloudflare API token that can deploy the named Workers and manage Worker secrets. |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID. |
| `CF_DJANGO_SECRET_KEY` | Unique random Django production key. |
| `CF_TOKEN_SIGNING_KEY` | Separate unique random bearer-token signing key. |
| `CF_DJANGO_ALLOWED_HOSTS` | Comma-separated exact API hostnames; no wildcard. |
| `CF_CORS_ALLOWED_ORIGINS` | Exact HTTPS frontend origin(s), without paths or trailing slash. |

Add these GitHub Actions **variables**:

| Name | Value |
| --- | --- |
| `CLOUDFLARE_DEPLOY_ENABLED` | Keep unset until all release gates below are resolved; set to `true` to enable deploy after successful CI on `main`. |
| `CLOUDFLARE_HYPERDRIVE_ID` | ID of a Hyperdrive configuration attached to the production PostgreSQL database. |
| `CLOUDFLARE_API_ORIGIN` | HTTPS origin for the deployed API Worker, with no path, for example `https://api.example.com`. |
| `CLOUDFLARE_FRONTEND_ORIGIN` | HTTPS origin for the deployed frontend, with no path, for example `https://journal.example.com`. |

Create the GitHub Environment named `cloudflare-production` and configure
required reviewers and deployment branch restrictions before setting
`CLOUDFLARE_DEPLOY_ENABLED=true`. The workflow runs after successful CI on
`main`; the Environment protection rule is the human promotion gate.

Create a production PostgreSQL database reachable by Cloudflare Hyperdrive,
then create the Hyperdrive configuration using its production host, database,
username, and password. The config ID goes in the GitHub variable above; the
database credential is stored in the Hyperdrive resource, not in this
repository or GitHub workflow. Configure database network access and backups
before enabling deploys. Apply Django migrations from a trusted environment
with controlled database access before using the app; this proof of concept
does not run migrations automatically.

The Worker uses `APP_ENV=production`, `DJANGO_DEBUG=false`, and
`AI_PROVIDER_MODE=openai`; fake AI responses are never enabled. `AI_API_KEY`
is blank unless a real provider is intentionally configured later. The API
host and CORS values are injected as Worker secrets because these are
environment-specific. Do not put signing keys or database credentials in
frontend build variables.

## Release gates and limitations

1. **Hyperdrive has two distinct TLS hops.** Cloudflare's Python Workers
   example uses `ssl=False` for the Worker-to-Hyperdrive socket. Hyperdrive
   separately uses TLS to connect to the PostgreSQL origin; its default origin
   mode is `require`, and the Hyperdrive resource must retain a TLS-required
   mode. The production check accepts `sslmode=disable` only when the isolated
   adapter sets `DATABASE_CONNECTION_KIND=cloudflare-hyperdrive`. All ordinary
   production PostgreSQL connections still require `require`, `verify-ca`, or
   `verify-full`. Confirm the Hyperdrive origin TLS setting when provisioning
   the resource.
2. **The local Cloudflare build has not been validated in this environment.**
   The current frontend dependencies use the Lovable Vite wrapper with Nitro
   configured for Cloudflare by default. The production output path in
   `frontend/wrangler.jsonc` must be verified by a frontend build and a
   Wrangler dry run before deployment is enabled. The production Cloudflare
   Vite plugin migration is intentionally not mixed into local/Docker config.
3. **Account and resource checks remain unverified.** No Cloudflare account,
   API token, PostgreSQL host, Hyperdrive ID, domain, or production endpoint
   was available for this change. Workers Python remains a documented beta;
   package bundling for the application's Django and PostgreSQL driver must be
   confirmed in the target account/runtime.
4. **Production database migrations are manual.** Apply and verify migrations
   from a trusted administrative environment before enabling the new Worker.
5. **Deployment health checks only verify HTTP availability.** The workflow
   requests `/api/health/` and the frontend root after deployment. The current
   API health view does not test the database. Before production use, verify a
   real database-backed request and an authorized login flow against staging.

The required account and resource configuration is therefore currently
unconfigured, and a successful production deployment must not be claimed.

## References

- [Cloudflare Django on Python Workers](https://developers.cloudflare.com/workers/languages/python/packages/django/)
- [Cloudflare Python Workers packages and Pywrangler](https://developers.cloudflare.com/workers/languages/python/packages/)
- [Cloudflare Hyperdrive with Python Workers](https://developers.cloudflare.com/hyperdrive/examples/python-workers/)
- [Cloudflare Hyperdrive TLS configuration](https://developers.cloudflare.com/hyperdrive/configuration/tls-ssl-certificates-for-hyperdrive/)
- [Cloudflare TanStack Start guide](https://developers.cloudflare.com/workers/framework-guides/web-apps/tanstack-start/)
- [Cloudflare Workers GitHub Actions guide](https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/)
