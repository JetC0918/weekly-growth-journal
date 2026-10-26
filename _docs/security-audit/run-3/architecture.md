# Predeployment audit architecture — run 3

Date: 2026-10-26 (Asia/Singapore). Target: `C:/Users/crab/py2/weekly-growth-journal`.
Baseline local/GitHub main: `b7c0ae9d6d0fb228db2994201ab2a936069a9f8f` (206 tracked files).
Artifacts use the repository's existing `_docs/security-audit/run-N` convention to remain reviewable inside the writable workspace. No home-directory runs exist; runs 1 and 2 both contain empty findings lists and explicitly limited static coverage. Their frontend advisory totals are historical, not current findings.

## Application and trust model

Private account-based weekly journal: register/login, draft reflection, AI follow-ups and report, editable insights, commitments, history and deletion. Comparable class is private account-based note/journal software (Day One/Joplin-style server account separation); comparisons describe expectations, not claims about their internals. Users may alter their own data; another user's ID must not grant access. Operators controlling keys/database/provider configuration are trusted. Sending selected reflection content to the configured AI provider is designed behavior.

Active frontend: TanStack Start, React 19, TypeScript, Bun (`frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/server.ts`). Application export selects the real HTTP GrowthService (`frontend/src/services/index.ts`); browser tokens stay in module memory (`auth.ts`), data routes disable SSR. Mock service remains documented/tested.

Active API: Django 5.2/DRF/PostgreSQL (`backend/config/settings.py`, `urls.py`, `backend/journal/{models,serializers,views}.py`). Default signed bearer authentication and IsAuthenticated. HMAC-SHA256 signature plus expiry and active-user lookup (`backend/accounts/{tokens,authentication}.py`). Register/login explicitly public; health public; Django admin uses framework sessions/CSRF. Journal queries scope to request.user and related reports/commitments to owned reviews. Operator keys/environment are the configuration boundary.

## Input surfaces and sinks

- HTTP: `/api/auth/register`, `/api/auth/login`, `/api/health/`, `/admin/`, and journal routes in `backend/journal/urls.py`: reviews create/list/get/update/delete, follow-ups, complete, reports, insight updates, previous commitments, account-data deletion.
- Stored text: reflection, report/insight corrections, commitments; Django ORM storage and React rendering. Follow inputs through serializer validation, ownership, provider and browser output.
- AI transport: `backend/feedback/follow_ups.py`, `reports.py`; configured provider URL/key, user reflection sent upstream, parsed provider results stored. Fake mode supports offline synthetic tests.
- Settings: environment variables for secrets, hosts, CORS, database, TLS, provider, telemetry; fail-closed production checks in `backend/config/checks.py`.
- No application uploads/import/export/webhooks, custom WebSocket server or arbitrary user-supplied fetch URL were identified during recon.
- Local tooling: `mcp-server/src/server.py` stdio JSON-RPC with fixed document read allowlist; `agent-hooks/check_staged_changes.py` content guardrail; markdown extension pack. These are developer-side surfaces.

## Deployment and secondary surfaces

Docker backend (`backend/Dockerfile`) migrates then launches Django ASGI via Uvicorn. Frontend Docker starts generated Nitro Node server. `docker-compose.yml` is development-oriented. Local-only OTLP/Grafana/Loki/Tempo/Prometheus configuration is under `observability/`; application instrumentation in `backend/config/telemetry.py`.

Cloudflare is a gated, unverified proof of concept: Python Worker `backend/cloudflare/src/worker.py` adapts Django WSGI and Hyperdrive; bundle script copies only accounts/config/feedback/journal. Separate Python manifest/lock must also be reviewed. Frontend Worker uses `frontend/wrangler.jsonc`. Compatibility, migrations, transaction/locking behavior, DB TLS, edge access and telemetry need deployment evidence. Deployment workflow is disabled by repository variable until gates are satisfied.

Legacy FastAPI prototype (`backend/app/`, `backend/tests/`) has in-memory seeded accounts and a fixed development key; not reached by supported Django/Docker/Worker entry points. Review as retained source and assess coordinated retirement, not as a live auth bypass.

GitHub: private repository `JetC0918/weekly-growth-journal`; main matches local base; no open PRs. Latest CI run 40280045096 succeeds, deployment 40280133581 is skipped. Dependency scans are continue-on-error and upload artifacts. Main branch reports protected=false and repository rulesets list is empty; direct protection endpoint returns integration 403. Hosted controls beyond accessible API must be marked unverified.

## Run focus

Previous runs did not dynamically attack endpoints and did not retrieve current hosted scan evidence. Focus this run on auth/token lifecycle and cross-user boundaries; provider/logic/concurrency/resource abuse; frontend/SSR injection and cross-origin trust; deployment/CI supply chain, current lockfile advisories and git-history secret checks. Confirm runtime claims with synthetic data and independently disprove/verify findings. Do not change dependencies without approval or deploy/publish.
