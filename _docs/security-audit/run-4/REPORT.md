# Predeployment security audit — run 4

**Date:** 26 October 2026 (Asia/Singapore)

**Target:** JetC0918/weekly-growth-journal (private)

**Local source audited:** `5684e13aa88613c8338b97e529d289db5969dadd`, `codex/predeployment-audit-cleanup`; clean working tree at intake.

**GitHub main observed:** `b7c0ae9d6d0fb228db2994201ab2a936069a9f8f`. The hardened local revision has not been pushed or merged. Output follows the existing repository series at `_docs/security-audit/run-4`.

## Assessment

**Hold launch. No confirmed exploitable application vulnerability survived this run's hunting and independent candidate validation.** The hardened local dependency scans are clean and production startup/ownership checks resisted synthetic tests. GitHub now enforces a main ruleset and Dependabot alerts are enabled. However, GitHub still holds the old source and dependency backlog, both configured origin values fail the workflow's origin validator, and the configured Workers currently serve **Hello World!** rather than the journal application. No production app authentication, persistence, gateway or actual Python Worker runtime has therefore been attested.

The baseline is a private account-based journal/notes service: users may control their own reviews and reports; knowing another user's identifiers must not expose their data. Operators controlling database/signing/provider configuration are trusted. Day One/Joplin-style private notes are category comparables, not assertions about those products' implementation. Prior runs 1/2 had empty findings; run 3 rejected an unverified deployed-key bypass and a token-revocation contract claim. This run verified the local startup/password/dependency fixes and emphasized concurrency, session transitions, normalization, and actual release configuration.

## Confirmed application findings

| Severity | Finding | Result |
| --- | --- | --- |
| — | No independently validated, exploitable application vulnerability found. | This does not establish absence of vulnerabilities. |

Two tested exploit claims were rejected and retained in `findings.json`: cross-account report disclosure through stale browser responses, and victim account compromise through username normalization. The real reliability/hardening behavior behind them is described below; it is not severity-inflated into a compromise.

## Launch blockers and acceptance evidence

| Gate | Current evidence | Required before launch |
| --- | --- | --- |
| Hardened revision is unpublished | Fresh GitHub branch read shows main at b7c0ae9; no open PR. Its CI source still has dependency-scan `continue-on-error: true`. The local fixes are at 5684e13. | Publish the hardening branch through a reviewed PR; require all five checks on the exact release revision. Do not use the old green CI run as evidence for these fixes. |
| Origin variables fail validation | `CLOUDFLARE_API_ORIGIN` and `CLOUDFLARE_FRONTEND_ORIGIN` both end in `/`. The workflow rejects any parsed path at `.github/workflows/deploy-cloudflare.yml:77–81`; a fresh check returned false for both. | Set exact HTTPS origins without the final slash (values below), then rerun configuration validation. Secret CORS allowlist contents were not read and also need verification. |
| Configured Workers are placeholders | Native TLS-verified checks reached API health, API reviews, and frontend root. HEAD returned HTTP 200/text/plain without reading a body; bounded GET returned exactly the same 12-byte `Hello World!` body on all three paths. | Deploy the real application to a staging target, then prove the journal flow, owned data isolation, and expected API contract. HTTP 200 alone is insufficient. |
| Runtime/data/edge readiness unproved | Actual Hyperdrive origin TLS, migrations, database privileges/restore, Worker driver/transactions, private gateway/MFA/routing and edge admission/spending controls were not inspected. Workflow does not run migrations or provision `AI_API_KEY`; that secret may be configured separately in Cloudflare, which was not read. | Verify these against the selected deployment and retain evidence. Confirm provider configuration and fail-safe handling without using customer data. |

Correct non-sensitive origin values:

| Variable | Value accepted by the origin check |
| --- | --- |
| `CLOUDFLARE_API_ORIGIN` | `https://weekly-growth-journal-api.fiero19892.workers.dev` |
| `CLOUDFLARE_FRONTEND_ORIGIN` | `https://weekly-growth-journal-frontend.fiero19892.workers.dev` |

The current deployment smoke step (`deploy-cloudflare.yml:165–171`) only uses curl's HTTP-success check, so it accepts these placeholder responses. Strengthen it to require the exact health JSON `{"status":"ok"}`, the expected frontend output, unauthenticated API rejection, and a synthetic authenticated journal journey. A successful head/root response does not validate the app.

## Fresh dependency and secret-pattern scans

| Exact scope | Fresh result |
| --- | --- |
| Local root Python lock export | 42 applicable package records, zero known advisory entries; exit 0. |
| Local isolated Cloudflare lock export (all groups) | 17 applicable package records, zero known advisory entries; exit 0. |
| Local frontend Bun lock | Empty advisory result `{}`; exit 0. |
| Current GitHub main frontend lock, fetched at b7c0ae9 | **25 entries / 18 distinct advisory URLs / nine package names**; exit 1: 1 critical, 14 high, 9 moderate, 1 low. |
| Tracked text and reachable Git history | 176 tracked files; 24 reachable local commits; 321 unique blobs, two binary blobs skipped; zero matches from the repository's high-confidence secret patterns. |

The old main package names remain `@vitest/mocker`, `brace-expansion`, `js-yaml`, `launch-editor`, `nanoid`, `shell-quote`, `source-map-js`, `vite` and `zod`. These are advisory-database severities, not 25 demonstrated app exploits; run 3 documented the predominantly development/build-tool reachability. Their local updates now scan clean, but they are not yet on main.

Scans used exact frozen requirement exports and Bun 1.4.4 (matching CI); the official Bun release archive SHA-256 was verified as `cd2c0fccc78f3ede1f50ca827a15f063eda13d4d150a3d0674f4f6e323d864a5`. Python audit used advisory lookup without installing the app's requirements; platform-marker inactive entries are not claimed scanned. Ephemeral scanner dependencies/caches are ignored inside this run's output. No project dependency was changed. Regex history scanning is not entropy/binary/LFS/unreachable-object scanning or proof that no credentials ever existed.

## GitHub controls: fresh observations

- **Main protection now active:** ruleset [25871818](https://github.com/JetC0918/weekly-growth-journal/rules/25871818), targets only main, no bypass actors; requires one approval, dismisses stale approvals, requires review of the last push, and requires all five checks from GitHub Actions. Deletes and force pushes are blocked. Strict up-to-date-before-merge is false; consider enabling it. No destructive enforcement trial or human PR approval was performed.
- **Dependabot alerts enabled**, no open alerts returned. This does not contradict the Bun result: alert coverage/dependency-graph support is different from a direct Bun audit.
- **Code scanning explicitly still disabled** (API 403 with that message). **Secret-scanning status is not established by this run:** repository metadata returned `security_and_analysis: null`; no actual secret-alert content was requested. The previous disabled observation is historical, not reused as a fresh status. Availability of private-repository scanning depends on the GitHub plan.
- **Production environment:** allows only main; no required-reviewer rule returned. Private-repository reviewer availability is plan-dependent. Main PR review currently supplies a human review point, but no actual human review is recorded.
- **Deployment remains off:** repository variable list is empty; environment `CLOUDFLARE_DEPLOY_ENABLED` is now **false**, superseding the earlier true screenshot. The job-level gate expects a repository variable; environment variables arrive after job start ([GitHub variable scope](https://docs.github.com/en/actions/reference/workflows-and-actions/variables)). Keep the repository switch unset/false until launch gates pass.
- Latest actual [CI run 40280045096](https://github.com/JetC0918/weekly-growth-journal/actions/runs/40280045096) passed on old main; [deployment 40280133581](https://github.com/JetC0918/weekly-growth-journal/actions/runs/40280133581) was skipped. A newer dependency-graph update is not a new application CI/deployment run.

## Reproduced hardening/reliability notes

1. **Canonical username representation is inconsistent.** `accounts/serializers.py:40–43` validates password similarity against raw input; numeric username `31415.9265` with password `"31415.9265"` registered (201), while the string username was rejected (422). `accounts/views.py:24,35` casefolds before Django applies NFKC, so `audituser` and `𝐀udituser` produced distinct `audituser`/`Audituser` accounts; the second could not log in while the first remained usable. Independent validation found no victim takeover, victim login denial, or data access. Use one canonical validated string for policy, uniqueness, creation and login, and reconcile existing collisions before adding a database constraint.
2. **Stale responses can affect a newer browser session.** A deferred A request returning 401 after B logs in expires B through `httpService.ts:65`/`auth.ts:77`. Explicit old mutation callbacks can recreate old report cache entries (`report.$reviewId.tsx:65`). Ordinary queries are cancelled on clear, and the report route's owned-review loader/null guard prevented old content from rendering; no remote actor capability or cross-account write was proved. Bind requests/callbacks to a session generation and ignore obsolete responses.
3. **Report generation uses an earlier snapshot.** Editing a review during fake-provider work stored an old-evidence report beside the edited review. Deleting during that work produced a generic 500 without resurrecting data or affecting another account (`journal/views.py:169,182–190`). Consider a version check and normal cancellation/not-found handling; same-account simultaneous insight JSON edits can also lose changes.
4. **Operational safeguards still need deployment evidence.** Token compromise recovery remains 24-hour stateless-bearer/deactivation based; password changes do not revoke existing tokens. Production HTTPS redirect/HSTS/secure session+CSRF cookies remain standard Django warnings, not startup errors. No application quotas, provider output-token budget or response-size cap exist; edge/provider budgets must be verified. Optional Lovable error hooks and actual telemetry retention/redaction need deployed review. Container non-root execution matters if that deployment target is selected.

## Positive patterns and verification limits

Current-code synthetic probes confirmed cross-user review/report/commitment/delete isolation, active-account bearer checks, malformed/forged-token rejection, role injection rejection, password validation, and real ASGI/WSGI startup refusal for bad production configuration. Stubbed Worker adapter checks validated binding-to-Django integration; they are **not** Cloudflare/Pyodide runtime proof. AI context included owned history only and did not dereference foreign commitment IDs. Strict provider output and React text rendering retained their boundaries. A 3 MiB authenticated body was rejected before persistence. Independent QueryClient/router checks rejected the client disclosure hypothesis.

The run used three recon scopes, three hunting scopes, two independent candidate validators and final independent report verification. Initial hunting workers hit a service usage limit; after the user's continue request they completed. One browser probe initially used Node server conditions; its result was discarded and replaced with browser-conditioned testing. Independent validation corrected a mock's wrong-owner 404 assumption: the real GET returns null200 and the loader throws notFound; the disclosure verdict remains rejected.

No application source, GitHub setting, customer record, or provider configuration was changed; no push/deploy/real-provider request occurred. Passive origin reads were unauthenticated and bounded; arbitrary body content was not retained. Python TLS checks failed local certificate validation, while native curl succeeded with verification enabled and identified the placeholders; this is not evidence that the site's public certificate is expired. No full rendered production journey, real PostgreSQL concurrency/restore test, container OS-image vulnerability scan or actual gateway security assessment was completed. See `evidence/verification.md`, `evidence/scan-summary.json` and raw evidence for exact scope.
