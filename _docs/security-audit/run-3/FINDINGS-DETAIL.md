# Detailed validation — run 3

No MEDIUM-or-higher application vulnerability survived independent validation. Exact attack requests are therefore not presented as confirmed exploits.

## Rejected claim A: deployed authentication bypass from default production keys

Observed code path:

1. `backend/config/asgi.py:7` / `wsgi.py:7` construct Django handlers.
2. `backend/config/settings.py:9–11,117` loads production mode but retains development fallbacks when key variables are absent.
3. `backend/config/apps.py:8–12` imports checks; `checks.py:61` registers them as deployment-only, not startup enforcement.
4. `checks.py:86–89` rejects development keys only when deployment checks run.
5. `backend/Dockerfile:16` launches migrations/Uvicorn without executing deployment checks.

Two reviewers reproduced callable production handlers with default keys using synthetic configuration and no real database. Explicit checks returned E003/E004/E006/E009/E011/E012. This confirms the guard gap. It does not show any live instance has absent key configuration, an exposed origin, or a bypassed private gateway.

Counter-evidence: `_docs/private-deployment.md:25–35,50–52` requires deployment checks; `backend/cloudflare/src/worker.py:20–29,40–49` requires and injects key/host/CORS bindings. Under the skill's source-visibility rule, **rejected as a confirmed deployed auth bypass**, retained as a release blocker. The expected fix is automatic validation before serving traffic and negative staging startup checks. A baseline private journal must validate its chosen deployment configuration; comparing unrelated default-development settings does not establish an attack.

## Rejected claim B: password change violates a promised bearer-revocation boundary

Observed code path:

1. `backend/accounts/tokens.py:18–28` creates subject/expiry-only bearer tokens with the 24-hour lifetime at line 11.
2. `tokens.py:31–47` validates signature and expiration, not password state.
3. `backend/accounts/authentication.py:22–32` looks up the active subject.
4. `frontend/src/services/auth.ts:136–140` sign-out clears browser state only.

Two synthetic runtime checks independently observed GET reviews status 200 before and after `set_password`, then 401 after account deactivation. This establishes a recovery limitation for an already acquired token. No token-acquisition vulnerability was found. The app has no reset/revocation API, and `_docs/architecture.md:42` explicitly describes local token discard. **Rejected as a violation of the stated session contract**; recommend token versioning/revocation before broader use. Password-backed account-session applications commonly bind recovery to server state; this implementation instead has a finite stateless-token lifetime, so operator recovery must account for it.

## Other rejected leads

- Stored XSS: installed React escaped supplied script/image content in both text and textarea output. The unused chart HTML escape hatch had no caller and was removed during scaffold cleanup.
- Cross-user access: twelve synthetic owned-object/report/commitment/deletion paths denied access and preserved victim data. Related ORM queries enforce ownership.
- MCP traversal: unknown keys including POSIX/Windows traversal and `__proto__` returned JSON-RPC -32602. File paths are selected from a fixed allowlist.
- Oversized AI input: Django rejected a 3 MiB body before provider invocation.
- OTel query leak: a synthetic secret marker was absent from actual in-memory exported middleware span attributes after redaction.
- Privileged fork checkout: upstream checkout's current unsafe-PR-checkout guard prevented establishing the classic workflow_run claim; missing explicit provenance checks remain hardening.
- Dependency critical-to-RCE inference: shell-quote's vulnerable `quote()` flow was not reached by the inspected editor's `parse()` caller. Raw advisories remain a release backlog, not confirmed application exploits.

## Independence and reproducibility

Recon, hunting, adversarial candidate review and final evidence QA used separate agents. Reviewers returned findings rather than writing audit artifacts. Synthetic DB checks never used the configured development/production database or a real AI provider. The retained `evidence/run_isolated_tests.py` runs existing Django tests against an explicit SQLite memory database. This can reproduce behavior checks, but cannot establish PostgreSQL row locking, gateway framing/cache behavior or deployed secrets. Findings JSON and the report intentionally distinguish these limits from confirmed facts.
