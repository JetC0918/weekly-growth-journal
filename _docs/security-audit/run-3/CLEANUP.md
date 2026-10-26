# Spring cleanup — 26 October 2026

## Removed

- **10 retired FastAPI source/test files:** `backend/app/**` and the two `backend/tests/` compatibility tests. Supported entry points already use Django; Cloudflare packaging copies only canonical Django packages. Removed tests covered the retired implementation, not active behavior.
- **40 unreachable frontend controls and one mobile hook:** TypeScript AST import analysis rooted in all 35 non-UI source/test files retained only button, card, input, label, sonner and textarea. No visible UI behavior was intentionally changed. Independent QA found no unresolved local TypeScript/JavaScript imports.
- **14 unused Python lock entries:** removed FastAPI, httpx, pytest and their unused transitive graph; root lock shrank from 58 to 44 entries. Uvicorn remains the active Django server. No dependencies were added or upgraded; frontend manifest/lock are unchanged.
- **Generated caches:** removed `.audit-uv-cache`, `.qa-uv-cache` and the isolated Worker `.uv-cache`: 3,898 files totaling 75,669,819 bytes (about 72 MiB). Removed source bytecode caches after verification; exact directories are retained in `evidence/removed-bytecode.json`. Recursive removals checked resolved workspace boundaries first.

There are **51 deleted source files** in `evidence/cleanup-manifest.json`. Current README/backend/testing/architecture/specialist references were updated. The generic frontend starter README now describes this application's actual commands and architecture. Historical workflow and audit records preserve their original statements.

## Retained deliberately

- Mock service and its tests: explicitly required by frontend instructions and useful as deterministic test support.
- Active Django tests, migrations, dependency locks, generated route tree, deployment configuration and observability stack.
- Prior audit runs, product/process/design documentation and local extension tooling: useful evidence or maintained functionality.
- Installed development environments/dependencies: these are not application source clutter. Generated cache cleanup is recorded separately when performed; no private database or environment file was deleted.
- Frontend dependency graph: source scaffolding was pruned, but package removal/upgrades need compatible Bun lock regeneration and advisory remediation. The audit does not claim those packages are fixed by deleting components.

## Verification

Existing Django unit checks, frontend tests/lint/production build and Python lock consistency passed. Final independent QA and the explicitly limited synthetic-database test run are recorded in `evidence/verification.md`. The original baseline's hosted PostgreSQL/container checks passed, but those hosted results do not validate this unpushed cleanup revision.
