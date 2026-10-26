# Predeployment security audit — run 3

**Date:** 26 October 2026 (Asia/Singapore)
**Repository:** [JetC0918/weekly-growth-journal](https://github.com/JetC0918/weekly-growth-journal), private
**Audited baseline:** `b7c0ae9d6d0fb228db2994201ab2a936069a9f8f`; local and GitHub main matched. Cleanup is a separate local change on `codex/predeployment-audit-cleanup`.

## Executive assessment

**Recommendation: hold deployment until the release gates below are resolved.** This run found no independently validated, exploitable application vulnerability in the reviewed code paths. It did confirm a startup configuration-validation gap, an unresolved frontend dependency advisory backlog, and weak GitHub release enforcement. These are material readiness concerns, not evidence that a live service has been compromised. No production service was attacked or deployed. The API's ownership enforcement, bearer verification, strict provider-output handling and browser escaping performed well in source review and synthetic runtime checks.

## Findings

The comparison baseline is a private account-based journal/notes service (Day One/Joplin-style account separation), rather than a public CMS. Users may edit and delete their own material; knowing another user's identifier must not confer access. Operators who control database/signing/provider configuration are trusted. This code meets the ownership expectation in the tested paths; its release enforcement and credential-recovery procedures still need work. No claim is made about those products' internal implementations.

| Severity | Confirmed application vulnerabilities | Status |
| --- | --- | --- |
| — | None survived adversarial validation. | This does not establish absence of vulnerabilities. |

`findings.json` records two investigated and rejected vulnerability claims. Their underlying limitations remain documented below. Advisory database severities are reported separately and are **not** application exploit severities.

## Required before launch

| Priority | Observed issue | Required action / acceptance evidence |
| --- | --- | --- |
| Release gate | Production startup does not execute deployment checks. | Enforce configuration validation before serving traffic; verify the actual container refuses invalid settings. |
| Release gate | Frontend audit reports 25 entries, including a critical-rated dependency advisory. | Update affected dependency paths compatibly or record justified, reviewed reachability exceptions. Retain a fresh scan plus successful test/build results. |
| Release gate | Dependency scan failures do not fail CI. | Make unresolved release-relevant advisories and scanner failures block release, using explicit reviewed exceptions if needed. |
| Release gate | Main is unprotected; production Environment has no required reviewer. | Require PRs and passing checks on main, protect the release environment, and verify enforcement with a non-destructive trial. |
| Release gate | No selected live deployment was available to inspect. | Verify private identity gateway/MFA, allowed users, HTTPS, CORS, origin restrictions, database TLS, backups/restore and runtime compatibility. Keep deployment disabled until then. |

### Configuration guard gap: reproduced, conditional on misconfiguration

`backend/config/settings.py:10,117` supplies known development signing keys regardless of `APP_ENV`. `backend/config/checks.py:61` registers production checks only for explicit deployment checks. `backend/config/asgi.py:7`, `wsgi.py:7` and `backend/Dockerfile:16` do not execute them before accepting traffic. Independent synthetic startup checks set production mode, disabled debug, removed secret/database/host/CORS settings and still obtained callable ASGI/WSGI handlers. Explicit deployment checks separately returned `config.E003/E004/E006/E009/E011/E012`.

A misconfigured container could therefore serve with development signing keys. **This audit did not establish that any deployed service uses them.** The private deployment runbook requires `check --deploy`. This is a confirmed guard gap and release blocker, not a confirmed deployed authentication bypass. Production secrets, gateway and database TLS were not read or verified.

## Dependency results and reachability

The baseline's [successful hosted CI run](https://github.com/JetC0918/weekly-growth-journal/actions/runs/40280045096) uploaded [the dependency artifact](https://github.com/JetC0918/weekly-growth-journal/actions/runs/40280045096/artifacts/12631857585). Its downloaded ZIP SHA-256 matched GitHub's recorded digest: `07184e0bcfc36300f35b3e5e946e37b53a810273c6500c1f8a69023d735979f3`. Raw JSON is retained in `evidence/`.

| Scan | Observed result | Scope / limits |
| --- | --- | --- |
| Hosted baseline Python | No known vulnerabilities; 76 result records. | Includes scanner/tool dependencies, not 76 repository lock entries. |
| Hosted frontend | **25 advisory entries across nine package names; 18 distinct advisory URLs.** | 1 critical, 14 high, 9 moderate, 1 low. Frontend lockfile is unchanged by cleanup. |
| Fresh cleaned root Python lock | No known vulnerabilities. | Exact pinned requirement export; includes platform markers. See `root-pip-audit.json`. |

The frontend scan's nonzero exit is visible in the hosted job log, while `.github/workflows/ci.yml:110,116` allows both dependency scans to continue. A green workflow therefore does not mean the dependency audit passed. No dependencies were upgraded as part of this audit.

| Package | Locked affected version(s) | Actual usage / assessment |
| --- | --- | --- |
| `@vitest/mocker` | 4.1.11 | Vitest tooling. Advisory affects dev-server mock registration; no production mock-registration endpoint found. |
| `brace-expansion` | 1.1.16, 5.0.8 | Transitive minimatch/lint/tool globbing. No remote journal input to expansion established. |
| `js-yaml` | 4.3.0 | ESLint/XML/build tooling. No user YAML input surface found. |
| `launch-editor` | 2.14.1 | TanStack devtools editor helper. Do not expose development tooling publicly. |
| `nanoid` | 3.3.16 | PostCSS build identifier generation. No attacker-selected generator size found. |
| `shell-quote` | 1.10.0 | Critical-rated `quote()` advisory. Installed editor callers use `parse()`; no app-controlled input reaching vulnerable `quote()` demonstrated. |
| `source-map-js` | 1.2.1 | PostCSS/Tailwind build/source maps. No attacker-supplied source-map endpoint found. |
| `vite` | 8.1.5 | Development/build server. Review development exposure separately from generated production runtime. |
| `zod` | 3.25.76 direct; 4.6.5 nested | App uses object/string validation for week search; nested schemas occur in router/build tooling. No hostile collection reaching the advisory's array-validation path established. |

These remain dependency maintenance items; **25 entries do not mean 25 exploitable application vulnerabilities**. The critical advisory requires a specific `quote()` comment-token flow ([maintainer advisory](https://github.com/advisories/GHSA-pqg4-j6r4-53mv)). Other reviewed primary advisories identify fixes including [mocker 4.1.12](https://github.com/advisories/GHSA-qxg6-89mg-rqv8), [Vite 8.1.6](https://github.com/advisories/GHSA-rq7h-c2jc-7f22) and [Zod 4.6.6](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5). Zod major-version migration requires compatibility work; do not blindly override all copies. Reachability analysis is source-based, not a production bundle attestation.

## GitHub review

| Control | Direct observation |
| --- | --- |
| Remote scope | Main and a prior readiness branch listed; no open PRs or releases. Main matched the local audited revision. |
| Main branch | `protected:false`, empty rulesets; authenticated CLI protection read returned `Branch not protected`. |
| Latest CI | Run 40280045096 succeeded; frontend advisory command exited 1 under continue-on-error. Unit/integration/frontend/container jobs succeeded on the baseline only. |
| Latest deployment | [Run 40280133581](https://github.com/JetC0918/weekly-growth-journal/actions/runs/40280133581) skipped. The repository deployment-enable variable was absent. |
| Dependabot alerts | GitHub API explicitly returned alerts disabled (403). |
| Code scanning | GitHub API explicitly returned code scanning not enabled (403). |
| Secret scanning | GitHub API explicitly returned secret scanning disabled (404). |
| Token permissions | Workflows declare `contents: read`; deployment credentials are scoped to the release job. |

The connector could not read several administration/security endpoints; authenticated GitHub CLI reads provided the statuses above. Secret values were not fetched. User/organization policies, collaborator privileges and Environment secret contents are outside verified coverage. `security_and_analysis:null` alone was not used to infer disabled controls.

Workflow provenance deserves explicit push-event and same-repository checks in addition to a successful-CI/main-name gate. A classic fork-checkout exploit was investigated and rejected because the current floating checkout v4 implementation includes the upstream unsafe-PR-checkout guard. Pin verified action revisions and retain explicit provenance checks; do not rely only on a mutable tag. See [GitHub's protection announcement](https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/).

## Other hardening and operational limits

- **Token recovery:** a bearer issued before a password change still worked afterward; deactivating the account rejected it. Tokens last 24 hours and do not bind to password state (`accounts/tokens.py:11–47`, `authentication.py:22–32`). Browser sign-out explicitly only discards local memory; no server revocation/reset endpoint is promised. Add token versioning or revocation and document account-compromise recovery. No independent token-theft weakness was established.
- **Registration:** the configured Django password validators are not called by registration; a common numeric eight-character password was accepted in a synthetic check. Decide and enforce the intended password policy. Apply edge limits to public login/register and provider operations; missing application limits alone were not treated as demonstrated compromise.
- **AI cost/concurrency:** the provider has a 15-second timeout, but no explicit output-token budget or per-user quota. Completion calls the provider before acquiring its persistence lock. Verify edge admission, spending limits and PostgreSQL races before release; repeat generation is supported behavior, not itself an authorization bypass.
- **Deployment:** Validate driver, migrations, transactions/row locks, provider networking and telemetry in staging. A root-page/health smoke check does not establish journal flow security. Make first-release and key-change ordering safe before launch.
- **Runtime exposure:** development Compose deliberately publishes database/API/frontend ports and uses development defaults. Keep it private. Containers have no explicit non-root user; harden the selected production image. Verify frontend frame policy and caching at the actual gateway; no confirmed clickjacking/cache leak was demonstrated.
- **Privacy:** synthetic OTel path/query redaction passed; actual exporter retention/access and exception/log redaction need a deployed check. Preview hooks can forward error/path details; verify they are absent or intentionally configured in production. AI receives selected own-account reflection/history by design; document provider privacy/retention.

## Positive patterns and validation

- DRF protects journal endpoints by default; object queries and report/history/commitment paths are scoped to the authenticated account.
- Bearer signatures use constant-time HMAC verification, expiry and active-user lookup. Missing, malformed, tampered, expired, non-ASCII and inactive-user tokens were rejected. Admin session cookies alone did not authorize bearer-only APIs.
- Twelve synthetic cross-user access attempts failed, preserving the victim's review/report/commitment. Role injection on registration was rejected; an untrusted Origin received no CORS authorization header.
- Provider responses have strict shape/type/evidence validation, safe errors and transactional storage; report regeneration preserves user edits. No model tool execution exists.
- React escaped supplied script/image text. MCP rejected path-traversal and unknown document keys while allowing its intended document. No application upload, arbitrary user URL fetch, raw SQL or user-shell sink was identified.
- Django rejected a 3 MiB request before invoking the provider. A synthetic secret in a query did not survive tested OTel span redaction.
- High-confidence secret-pattern scanning found no matches across **273 unique blobs in 21 reachable local commits**; one binary blob was skipped. This is not a full entropy/credential scanner or proof of no historical secrets.

See `FINDINGS-DETAIL.md`, `architecture.md` and the retained evidence for scope, commands, cleanup and independent review. Runs 1 and 2 had empty findings and narrower static coverage; this run adds dynamic checks and actual hosted evidence. Additional independent runs can still find missed paths.

## Verification and coverage limits

The whole tracked repository was inventoried, with focused source review of executable paths, migrations, configuration, workflows and developer tooling. Three recon scopes and three hunting scopes were followed by independent candidate validation and QA. One auth hunting agent's final turn was blocked by its service after returning runtime observations; no blocked exploit-generation attempt is represented as executed evidence. No live penetration test or production attestation is claimed.

Fresh Python scans passed. Cleanup validation and full-suite results are recorded in `CLEANUP.md` and `evidence/verification.md`. Local Docker access failed with a named-pipe permission error, so no fresh PostgreSQL/container runtime check occurred here. Isolated SQLite tests do not validate PostgreSQL locking semantics. No production keys, customer reflections, real-provider calls, cloud ingress or deployed browser journey were inspected. Container OS-image vulnerabilities, binary secrets, unreachable Git objects, remote-only historical refs and provider internals remain unscanned. Repeat advisory scans on the exact release revision and perform the staging checks above before release.
