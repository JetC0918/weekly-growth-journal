# Security audit scope — run 2

- **Target:** Weekly Growth Journal at baseline `676c00a`, with the task diff
  reviewed on 2026-10-26.
- **Application:** TanStack Start/React frontend, Django/DRF API, PostgreSQL,
  signed bearer auth, optional OpenAI-compatible provider, and local OTel stack.
- **Actors and boundaries:** anonymous callers can register/login and read the
  static health endpoint; authenticated users manage only their own journal
  records; operators supply environment secrets and database/provider settings.
  Inputs enter through JSON request bodies, path/query dates and IDs, environment
  configuration, stored reflections, and optional provider responses.
- **Key sources:** `backend/config/urls.py`, `backend/config/settings.py`,
  `backend/accounts/{authentication.py,tokens.py,views.py,exceptions.py}`,
  `backend/journal/{urls.py,views.py,serializers.py}`,
  `backend/feedback/{follow_ups.py,reports.py}`,
  `backend/config/telemetry.py`, and `frontend/src/services/auth.ts`.
- **Prior run:** run 1 found no confirmed source vulnerability and recorded a
  Python dependency correction plus 25 frontend advisories from an earlier Bun
  scan. This run focuses on auth/ownership, browser session handling, telemetry
  privacy, extension boundaries, and evidence quality.
- **Method and limits:** source inspection and an independent focused review.
  No live attack requests, frontend advisory scan, Docker telemetry walkthrough,
  or deployment test was completed in this session.
