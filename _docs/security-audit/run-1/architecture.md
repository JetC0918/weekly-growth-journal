# Security audit scope

- **Target:** Weekly Growth Journal repository at the working-tree revision on
  2026-10-26.
- **Application:** Personal web journal with TanStack Start/React frontend,
  Django/DRF API, PostgreSQL persistence, bearer-token auth, and optional
  OpenAI-compatible provider. The FastAPI app under `backend/app/` is
  transitional and not the active launch path.
- **Actors:** anonymous callers can register, log in, and read the static health
  response. Authenticated callers can create and manage their own journal data.
  The API views filter journal records by authenticated user. Operators control
  Django configuration, database credentials, and provider credentials.
- **Trust boundaries:** browser JSON to the API; bearer token to
  `SignedBearerAuthentication`; API to PostgreSQL; review content to the optional
  provider; deployment environment variables to Django settings. Key sources:
  `backend/config/urls.py`, `backend/accounts/views.py`,
  `backend/accounts/authentication.py`, `backend/accounts/tokens.py`,
  `backend/journal/views.py`, `backend/journal/serializers.py`,
  `backend/feedback/follow_ups.py`, and `backend/config/checks.py`.
- **Input surfaces:** registration/login request bodies; all authenticated
  review, insight, commitment, report, and deletion endpoints; date and UUID
  path/query values; environment configuration; and optional upstream provider
  responses. SQL is issued through Django ORM. The API emits JSON through DRF.
- **Deployment baseline:** local Docker Compose with PostgreSQL. Production
  checks enforce explicit HTTPS CORS origins, non-wildcard hosts, separate
  secrets, and TLS database config. No production host is configured.
- **Audit method:** manual source review of auth, serializer, journal ownership,
  provider, configuration, deployment guidance, and working-tree CI. No
  dynamic attack attempt or production environment test was performed. The
  dependency scan history and the current CI scope are recorded in `REPORT.md`.

No prior security-audit artifact was present in the repository at the start of
this run.
