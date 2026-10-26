# CI and deployment

## Continuous integration

The `CI` workflow runs for pull requests and pushes to `main`. It checks Django
unit and PostgreSQL integration tests, frontend tests/lint/typecheck/build,
container configuration/builds, dependency audits, and tracked-content
guardrails. A successful workflow verifies only the checks reported for that
revision.

## Render deployment

The primary cloud deployment is defined in the root `render.yaml` Blueprint.
It deploys the frontend and Django API from their existing Dockerfiles. Both
services use `autoDeployTrigger: checksPass`, so Render waits for repository
checks before deploying a commit. Service configuration and free-tier database
requirements are documented in [`render-deployment.md`](render-deployment.md).

The Blueprint provisions Render Postgres and connects it to the API through an
internal `DATABASE_URL`. It generates separate Django and bearer-token signing
keys. The database connection requires TLS. No Render account, database,
secrets, deployed services, or successful live journey are claimed by the
checked-in configuration alone. Render Free Postgres expires after 30 days;
review the retention limits in [`render-deployment.md`](render-deployment.md)
before storing personal data.

## Release verification

Before using the deployed service with personal journal data:

1. Confirm both Render services deployed the same intended Git revision after CI
   passed.
2. Verify the API health endpoint and the frontend root.
3. Use synthetic data to verify registration, login, review save/read/complete,
   report editing, commitment lookup, account isolation, and deletion.
4. Confirm the PostgreSQL migration state, HTTPS CORS preflight, logs, and
   telemetry privacy. Verify an encrypted backup and an isolated restore.
5. Record the revision, service URLs, migration result, smoke checks, telemetry
   evidence, and rollback result. Exclude journal content and credentials.

The health endpoint returns HTTP status only and does not prove database
readiness. A passing CI run or a healthy Render service does not replace the
synthetic end-to-end journey.
