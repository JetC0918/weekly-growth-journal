# Cloudflare deployment path

## Current state

The repository contains Cloudflare frontend/API Worker configuration and a
conditional production deployment workflow. Deployment is deliberately disabled
until its release gates are complete; this runbook does not claim a successful
Cloudflare build, external database, Worker, private-access policy, or production
URL. The local full-stack Docker Compose environment is the documented
end-to-end run path; its build could not be verified here because Docker Engine
access was unavailable.

The frontend is a TanStack Start/Nitro app. The API is Django 5/DRF with
PostgreSQL, psycopg binary wheels, database transactions, and row locking.
Cloudflare documents Django adapters for Python Workers, but Python Workers run
on Pyodide and package compatibility is still a constraint. This repository's
PostgreSQL driver, Django transaction/locking behavior, and OpenTelemetry
exporters must be proven compatible before selecting this as the production
runtime. Do not replace PostgreSQL with D1 without redesign: the current
application relies on PostgreSQL behavior and transactions.

## Staged release sequence

1. **Prove the runtime.** Build a disposable Python Worker from the current
   backend dependencies. Verify Django startup, psycopg connectivity through a
   test Hyperdrive binding, migrations, `select_for_update`, atomic rollback,
   outbound provider requests, and OTLP export. Record exact package versions,
   Worker compatibility date/flags, test evidence, and runtime limits. Stop if
   a required package lacks a supported Pyodide/PyEmscripten build or a required
   database feature does not behave as it does on PostgreSQL.
2. **Prepare isolated environments.** Create separate Cloudflare development
   and production Workers, frontend Workers, Hyperdrive bindings, and separate
   managed PostgreSQL databases. Keep production secrets out of GitHub logs and
   build-time frontend variables. Use the private access gateway for the
   personal app; configure exact HTTPS API host and CORS origin allowlists.
3. **Deploy development.** Build and deploy the frontend and API to development
   from one commit. Apply migrations in a controlled release step, then verify
   health, registration/login, review save/read/complete, report editing,
   commitment lookup, account isolation, and deletion using synthetic data.
4. **Check operations.** Verify TLS and CORS preflight, database TLS/backup and
   isolated restore, OTLP delivery, request-to-log trace correlation, dashboard
   environment/version filters, and alert behavior. Confirm that no journal
   content or secrets appear in telemetry.
5. **Promote the same revision.** After development checks pass, promote the
   exact tested source revision to production through the conditional workflow
   in `.github/workflows/deploy-cloudflare.yml`, gated by successful CI on
   `main`, after configuring required reviewers and branch restrictions for the
   `cloudflare-production` GitHub Environment.
   Apply production secrets and environment settings, verify health and the
   critical journey, and record the revision and outcome. Keep rollback
   instructions beside the release record.

### Account identity migration prerequisite

The account authentication hardening adds
`backend.accounts.0001_canonical_username_identity`. It builds a unique,
indexed canonical username key without renaming or deleting accounts. The
backfill stops before inserting identities if existing accounts normalize to
the same key; reconcile those accounts manually while preserving their journal
data, then rerun the migration. The deployment workflow does not apply database
migrations. Run this migration in a controlled staging/release step with old
registration writes quiesced across the backfill and application cutover, then
verify every account has an identity row before enabling registration. Do not
turn on production deployment until the actual Worker/database migration and
rollback behavior have been verified.

## Release evidence to record

For each release, record the commit/revision, build artifact digest, environment,
dependency lock revisions, migration result, deployment action/run link, health
and critical-journey outcome, telemetry/dashboard link, backup/restore check,
and rollback result if exercised. Do not record secret values, credentials,
reflection bodies, or provider payloads.

## Current blockers

- Worker configs and a conditional deployment workflow are checked in, but the
  workflow has not run and stays skipped until account-specific GitHub settings
  are configured. See [`cicd.md`](cicd.md).
- Django + the current `psycopg[binary]` driver and its PostgreSQL transaction
  semantics have not been built or exercised in Python Workers.
- The local OpenTelemetry stack does not provide a production collector,
  authentication, retention policy, alert routing, or an external dashboard.
- No Cloudflare account credentials, database instance, private access policy,
  or deployed environment is configured in this repository.

The first compatibility proof is a hard prerequisite to a truthful full-stack
deployment claim. If it fails, select a Django-compatible container host for
the API and keep the frontend on Cloudflare; do not force the Django service
into a runtime that cannot preserve its database guarantees.
