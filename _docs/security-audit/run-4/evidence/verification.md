# Verification record — audit run 4

## Scope and roles
Local baseline 5684e13aa88613c8338b97e529d289db5969dadd; branch codex/predeployment-audit-cleanup; intake tree clean. GitHub main read at b7c0ae9d6d0fb228db2994201ab2a936069a9f8f. This is a new audit, not a new implementation. Report artifacts only were written under run-4; tools/caches are ignored there. No application dependency or source change, live state change, secret-value read, real provider request, push or deployment occurred.

Three research recon agents mapped overview/trust/inputs. Three general hunters covered auth/config, business logic/AI, and browser/tooling. Their inherited context contained the architecture write verbatim and prompts required reading the full architecture and skill hunting/domain rules. Two fresh research validators independently checked the client/cache and username hypotheses. Initial hunter turns failed at a service usage limit; user requested continue, all three completed on retry. The primary assembled artifacts and performed read-only administration/scanner/passive checks, a recorded deviation from the repository process's pure-orchestrator role in order to preserve the audit skill's artifact ownership. Independent final report QA: PASS after reviewing the source and raw evidence. Its factual corrections clarified optional commitment data, HEAD versus GET response bodies, and the summary-file path. The reviewer reread the corrected artifacts and confirmed PASS before delivery.

## Fresh dependency scans
Exports, from repository root:
```text
uv export --frozen --no-hashes --no-emit-project --format requirements-txt --output-file _docs/security-audit/run-4/evidence/root-requirements.txt --cache-dir _docs/security-audit/run-4/evidence/tool-cache --quiet
uv export --frozen --project backend/cloudflare --all-groups --no-hashes --no-emit-project --format requirements-txt --output-file _docs/security-audit/run-4/evidence/cloudflare-requirements.txt --cache-dir _docs/security-audit/run-4/evidence/tool-cache --quiet
```
Both exited0. Set UV_TOOL_DIR inside the same output cache; ran:
```text
uv tool run --cache-dir <audit-cache> --from pip-audit pip-audit --no-deps --disable-pip -r <export> --format json --output <audit-json>
```
Tool version was pip-audit 2.10.1. Root and Cloudflare exited0, no known vulnerabilities:42 and17 applicable package records. Scanner warned that fully hashed requirement exports are preferable. This advisory-only lookup did not attest installed package hashes or inactive marker packages.

Official Bun1.4.4 Windows release archive was downloaded using verified HTTPS, checked against the GitHub release asset digest sha256:cd2c0fccc78f3ede1f50ca827a15f063eda13d4d150a3d0674f4f6e323d864a5, and executed only as audit tooling. It reported version1.4.4.
- From frontend/: portable Bun `audit --json` → evidence/bun-audit.json:exit0,{}.
- GitHub connector fetched frontend/package.json and bun.lock at exact main b7c0ae9 into ignored isolated output; immutable blob IDs/provenance retained in remote-source-provenance.json.
- From that isolated directory: portable Bun `audit --json` → evidence/remote-main-bun-audit.json:exit1 with25 advisory entries,9 names,18 URLs,1critical/14high/9moderate/1low.
No install/update was run against either application snapshot. scan-summary.json reconciles counts directly from raw JSON.

## Secret-pattern checks
```text
.venv/Scripts/python.exe -B _docs/security-audit/run-4/evidence/scan_repository.py
```
PYTHONDONTWRITEBYTECODE=1; exit0. Repository guard regexes scanned176 intake tracked files and321 reachable unique blobs across24 local reachable commits;2 binary blobs skipped;0 current/history matches. No matched values displayed. This is not an entropy/binary/LFS/unreachable-object/remote-only-history scan.

## Synthetic current-code checks
Hunters used inline no-file Python/Node commands and returned results; synthetic-checks.json records observed outcomes. Python configured SQLite :memory: before Django setup/migrations, synthetic accounts/keys, fake providers and PYTHONDONTWRITEBYTECODE=1. No actual configured journal database was used.
- Authentication/ownership:6 invalid registration422; anonymous and staff-cookie API401;6 malformed/tampered/non-ASCII bearer401;9 foreign object paths denied/null/no victim mutation; foreign-id save affected attacker row only; delete-all retained victim children; inactive bearer401.
- Startup:10 actual fresh ASGI/WSGI subprocess imports (valid then development keys/debug/empty CORS/unknown APP_ENV cases), plus4 Worker adapter checks with workers module stub. Valid returns app, invalid cases fail. Stub is not Worker/Pyodide proof.
- AI/logic:3MiB body400 before save; only own history in provider context, foreign commitment ID not forwarded/dereferenced; edit interleaving stores old evidence beside changed review; deletion interleaving returns generic500 without resurrection/victim mutation.
- Browser:installed QueryClient cancellation preserves B-only cache after A resolves; browser-conditioned router/loader testing blocks display of stale A report; actual source transpiled in memory reproduces old401 signing out current B.
- Independent auth validator reproduced raw-number similarity201 vs string422; Unicode collision second account401 while original account200 and original subject/data preserved.
- Independent client validator corrected the hunter's mock404 to actual GET null200 and tested the loader's null/notFound guard. Both reject user-visible report disclosure. Initial server-conditioned Node navigation probe was not counted.
Commands used synthetic fakes only, no live attacks or actual provider requests. These checks do not replace full rendered-browser, PostgreSQL locking or live Cloudflare verification.

Earlier hardening work in this same session ran the full Django suite67pass and frontend32pass/typecheck/lint/build on this exact unchanged local revision. Those are historical hardening checks, not newly executed full suites in run4; only the targeted audit probes/scans above are fresh.

## GitHub reads
Connector: current main/branches/ruleset/recent Actions/open PRs and exact remote source/lock snapshots. Administrative endpoints unsupported by connector used approved read-only gh API via github_snapshot.py. Default network call first failed; approved read-only calls succeeded.
- Main active ruleset25871818:main-only,no bypass,1review,stale/last-push safeguards,5required Actions contexts; strict up-to-date false.
- Environment:main-only branch policy,no required-reviewer rule.
- Repository vars:none; environment enable flag:false, both configured origins include trailing slash. Secret names only were read.
- Dependabot enable endpoint succeeded and open-alert list empty. Code scanning endpoint explicitly said not enabled403.
- security_and_analysis null did not establish current secret scanning status; no actual secret-alert endpoint/content requested.
- Main remains b7c0ae9 and latest app CI/deploy runs remain40280045096(success)/40280133581(skipped). No new exact-hardening hosted run.
Raw scoped JSON/provenance retained. No settings mutation or branch-protection destructive trial.

## Passive deployment checks and corrected TLS conclusion
```text
.venv/Scripts/python.exe -B _docs/security-audit/run-4/evidence/passive_origins.py
.venv/Scripts/python.exe -B _docs/security-audit/run-4/evidence/check_release.py
.venv/Scripts/python.exe -B _docs/security-audit/run-4/evidence/probe_public_response.py
```
Python urllib TLS verification failed with certificate-expired error. This was not treated as endpoint failure: native Windows curl without insecure flags independently completed TLS-verified HEAD/GETs. HEAD for API health/reviews and frontend root returned200 text/plain. Bounded unauthenticated GETs returned exact Hello World! for all3 paths:12 bytes, SHA256 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069. Only whitelisted placeholder content/hash/length persisted; arbitrary response bodies were not retained. These are placeholder resources, not evidence for journal API auth.
The exact workflow origin predicate independently rejected both configured origin strings because parsed_path='/' (release-check.json). No deployment was attempted.

## Structured output
```text
node C:/Users/crab/.codex/skills/security-audit/validate-findings.cjs _docs/security-audit/run-4/findings.json
```
PASS:2 rejected objects,0confirmed. Schema conformance is not factual verification. The final independent reviewer reconciled the verdicts, source references, raw counts, GitHub snapshot and passive response evidence; factual corrections were applied to the JSON and prose, then schema validation was repeated. No human release approval is implied.

## Remaining limits
Production key quality/secret values, private gateway and direct-route bypass, WAF/AI budgets, Hyperdrive origin TLS, database migrations/backup/restore, actual driver/Worker transactions, live journal/browser journey, real exporter retention, container OS-image advisories, binary/entropy secret scanning and unreachable/remote-only Git objects remain outside verified coverage. No human acceptance/release approval is recorded.

Final artifact checks: generated text was normalized to LF, trailing whitespace and blank EOF lines removed, and all JSON values compared before/after normalization. The first staged whitespace check failed on formatting only; it was rerun after this correction.
