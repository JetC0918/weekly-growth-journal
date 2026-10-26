# Verification record

Date: 26 October 2026, Asia/Singapore. Synthetic inputs only; no real provider or configured journal database was used.

## Cleanup checks

Engineer commands from repository root:

```text
.venv/Scripts/python.exe backend/manage.py check
.venv/Scripts/python.exe backend/manage.py test --exclude-tag=integration
uv lock --check --offline --cache-dir .qa-uv-cache
git diff --check
```

All passed: 29 non-integration tests, valid 44-entry lock. Lock regeneration used `uv lock --cache-dir .qa-uv-cache` after an offline attempt lacked metadata. Comparison showed only removals, no additions/upgrades. The temporary/generated caches were removed after verification; the exact cache-based command now needs a populated cache to repeat offline.

Engineer commands from `frontend/`, using installed tools because Bun was not on the local PATH; no environment flags:

```text
node node_modules/vitest/vitest.mjs run
node node_modules/eslint/bin/eslint.js .
node node_modules/vite/bin/vite.js build
```

Passed: 8 files / 32 frontend tests; lint 0 errors and 2 existing Fast Refresh warnings; client/SSR/Cloudflare production build. Independent TypeScript AST analysis verified all remaining local imports resolve and exactly six used shared controls remain. No product UI behavior change or screenshot-based UI acceptance is claimed.

## Independent Django QA

```text
.venv/Scripts/python.exe _docs/security-audit/run-3/evidence/run_isolated_tests.py
```

**Final result: 61 tests passed in 91.173 seconds**, exit 0, no system-check issues. The harness overrides the database to SQLite `:memory:` before initialization. It selects accounts/config/feedback/JournalAPITests. One deterministic journey that explicitly requires PostgreSQL is excluded. No product test was edited or weakened.

First attempt: 62 tests, 4 failures, 92.376 seconds. Three configuration tests conflicted with the harness-wide fake AI mode when they disabled debug; the fourth explicitly asserted PostgreSQL. Corrected only the audit harness: use openai mode with empty key (existing tests inject fake transports/settings), and select the 61 database-portable tests. Rerun justified by those harness failures. Neither attempt exercised a real provider.

Additional hunter runtime observations: twelve cross-user requests denied; malformed/tampered/expired/inactive bearer rejected; cookie-only API denied; role injection rejected; untrusted CORS origin denied; React text/textarea escaping passed; four invalid MCP document keys rejected; oversized body blocked; OTel query marker absent after redaction. These were inline synthetic harnesses, not retained standalone regression scripts. Their source-backed conclusions received independent review; they do not constitute production test results.

## Scans

- `python agent-hooks/check_staged_changes.py --tracked`: passed on the original 206 tracked files and on all 175 tracked files after cleanup/audit staging. Final staged whitespace check passed after normalizing generated audit text to LF line endings.
- `python _docs/security-audit/run-3/evidence/scan_history.py`: 21 reachable commits, 273 unique blobs, one binary skipped, no high-confidence pattern matches. Raw `history-scan.json` retained; no secret values printed.
- Downloaded hosted dependency ZIP; SHA-256 matched recorded artifact digest. Retained raw hosted JSON and ZIP.
- `uv export --frozen --no-hashes --no-emit-project --format requirements-txt --output-file _docs/security-audit/run-3/evidence/root-requirements.txt --cache-dir .audit-uv-cache`.
- `uv export --frozen --project backend/cloudflare --all-groups --no-hashes --no-emit-project --format requirements-txt --output-file _docs/security-audit/run-3/evidence/cloudflare-requirements.txt --cache-dir .audit-uv-cache`.
- Temporary scanner command, with `UV_TOOL_DIR` set inside `.audit-uv-cache/tools`: `uv tool run --cache-dir .audit-uv-cache --from pip-audit pip-audit --no-deps --disable-pip -r <exported-requirements> --format json --output <saved-audit-json>`. Both passed, no known vulnerabilities. Root output has 42 package records; Cloudflare 17; inactive platform/interpreter markers are excluded. Scanner warned that fully hashed pinned exports are preferable; lock export supplies exact versions but this advisory-only scan did not install or attest package hashes. Project dependencies were not changed by the scanner.
- `node C:/Users/crab/.codex/skills/security-audit/validate-findings.cjs _docs/security-audit/run-3/findings.json`: PASS, two rejected entries, zero confirmed findings. Independent reviewer verified reasons, prose, citations and package/advisory counts.

## GitHub and access

Connector reads: repository metadata, branches, main revision, rulesets, open PRs, releases, Actions runs/jobs/logs/artifact. Administrative/security endpoints unsupported by the connector were read through authenticated `gh api`; only status/configuration summaries were requested, never secret contents. Explicit disabled-feature API messages and the Environment branch policy were inspected. `gh variable list` confirmed no repository `CLOUDFLARE_DEPLOY_ENABLED` entry. See `github-review.json` for scoped observations.

Initial restricted network/cache reads failed; approved read-only network/scanner calls completed. FastCtx file inspection worked, but its shell ran against an unrelated environment despite the supplied cwd. Its unrelated output was discarded; actual repository commands used built-in execution with explicit Windows workdir. No unrelated environment was modified.

Docker server access failed with named-pipe permission denied. No fresh PostgreSQL/container, OS-image scan, Cloudflare build/runtime proof, actual gateway/cache/header check or live browser journey was performed. Baseline hosted CI passed those repository jobs at b7c0ae9 only; the cleanup/audit has not been pushed and has no hosted CI run yet.

## Roles and outcome

PM/recon supplied criteria and architecture; three independent hunters covered auth, logic/AI/privacy, and browser/operations; a separate validator rejected two unsubstantiated exploit classifications; engineer performed cleanup; independent QA verified source/import graph, raw scan counts, report/JSON/source agreement and the corrected 61-test run. Primary agent assembled reports, fetched scan/configuration evidence and ran checks, a limited departure from the process's pure-orchestration role to follow the audit skill's artifact-ownership requirement. An auth agent's final turn was service-blocked after runtime observations; no blocked action is represented as completed.

Scoped QA: **PASS**. Human review: **not recorded**. Release decision: **hold pending the report's gates**. No push, PR, external post, settings change or deployment was performed.
