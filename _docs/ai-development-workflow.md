# AI-assisted development workflow and evidence

Use [the work process](process.md) to move from a request through grooming,
implementation, review, verification, and delivery. This document records the
tools and evidence behind that work. Instructions describe intended behavior;
by themselves they do not prove that a role ran, a person reviewed a change,
a permission was enforced, or a check passed.

## Evidence available in this repository

- [`AGENTS.md`](../AGENTS.md) gives project commands and repository rules.
- [`process.md`](process.md) and [`team/`](team/) define PM, engineer, QA, and
  orchestrator responsibilities.
- [`task-template.md`](task-template.md) defines the task brief format.
- [`testing-guidelines.md`](testing-guidelines.md) describes test expectations.
- Git commits record repository changes and commit messages. They do not
  reconstruct prompts, approvals, or test results that were not saved.
- The dated records below capture these documentation tasks. They are not a
  reconstruction of earlier development. Missing historical prompts and human
  reviews remain unrecorded.

## Tool and MCP inventory

This inventory separates repository evidence from observations in the current
session. A tool being available to an agent does not mean this repository
installs, configures, or grants permissions to it.

| Tool or capability | Evidence/status | Use in this workflow |
| --- | --- | --- |
| FastCtx MCP file tools (`inspect_local_file`, `grep`, `glob`) | Observed in this task session; no tracked MCP server configuration was found. | Read only relevant context, batch related reads, and distinguish source files from generated output. |
| FastCtx `run` and Git | Observed for working-tree/revision inspection and documentation checks. Git history is repository evidence; the tool connection is session-provided. | Establish a baseline, inspect the diff, check scope, and record the actual command outcome. |
| Codex patch editing and PM/engineer/QA coordination | Session capabilities; [role pages](team/) and [process](process.md) are checked-in instructions, not executable agent configuration. | Assign bounded work, edit a reviewable diff, and retain role handoff evidence. Record only roles actually used in each task. |
| Django, Vitest, and pytest commands | Described in [`AGENTS.md`](../AGENTS.md), [`frontend/package.json`](../frontend/package.json), and [`pyproject.toml`](../pyproject.toml). | Available project checks when relevant and permitted; listing them is not evidence of execution. |
| External services and additional MCP tools | No repository configuration or use is asserted here. | Discover only when the task requires them; record the actual source, access scope, and any authorized external write. |

At the start of the second record below, inspection of tracked files at
`7d2f5bf` found no MCP server configuration, agent settings/permissions
configuration, Git hook setup, pre-commit configuration, or CI workflow.
Machine-wide or service-side settings may exist outside the repository; this
inspection does not establish their presence or absence.

During this task, a concurrent untracked
`.github/workflows/ci.yml` appeared in the working
tree. Its definition includes Django unit/integration, frontend test/lint/build,
and Compose configuration/build jobs. It was not created by this documentation
task. Inspecting that definition does not establish a successful run, enabled
required checks, or branch protection; none of those was verified here.

## Guardrails and enforcement

| Category | Current status and practical action |
| --- | --- |
| Checked-in repository policy | `AGENTS.md` requires reading testing guidance before writing tests and the design system for UI work, asking before adding dependencies, declaring dependencies in `pyproject.toml`, and committing regularly. Role and workflow documents define responsibilities. These are instructions for people/agents, not technical enforcement. |
| Check isolation | [Testing guidelines](testing-guidelines.md) call for deterministic fakes, isolated test data, no live AI calls in tests, and no developer/production database for tests. Apply these when tests are in scope; explicitly record a user's narrower verification instruction. |
| Session permissions | Access and approval controls come from the running tool environment. Record an observed restriction, approval request, or denial and its outcome when relevant. Do not infer unrestricted access from a successful read or claim the repository enforces a session rule. |
| Recommended handling | Supply the minimum relevant context; keep passwords, tokens, provider keys, and private reflection content out of prompts, logs, and task records. Use synthetic examples and safe error summaries. Inspect a concrete diff before an external write or destructive action and confirm it is covered by existing authorization. These practices are not installed controls. |
| Human review | Capture the reviewer's identity, date, decision, and requested corrections when supplied. AI QA PASS and an unchecked checkbox are not human approval. Pending review is an evidence status, not a new requirement to pause authorized work. |
| Automated hooks/CI | The repository CI workflow defines Django unit/integration, frontend test/lint/build, Compose/image builds, dependency advisory scans, and a tracked-content secret heuristic. Audit outputs are uploaded as artifacts; known dependency advisories are not suppressed from the artifacts. The Cloudflare deployment workflow is separate and conditional on successful CI on `main` plus repository configuration. Workflow definitions alone do not prove a successful run, required-check enforcement, or deployment; those remain unverified until observed. |

Privacy/security review is triggered by changes to authentication, ownership,
deletion/export, logs, provider context, secrets, or access configuration; see
[specialist routing](process.md#specialist-routing). Record concrete findings
and fixes, not a generic claim that the project is secure.

## Record format

For each substantive task, add a dated entry at intake and update it at the
handoffs. Keep the record short, but make the request, context, changes,
permissions, reviews, and observed checks traceable. Use `not applicable`,
`not run`, or `not recorded` where appropriate; do not invent missing evidence.

```text
### YYYY-MM-DD — short task name
- Task/prompt: source issue/chat; exact prompt or labeled excerpt/summary; retain important constraints.
- Baseline/scope: starting revision, existing changes, acceptance criteria, permitted files, exclusions.
- Context: relevant instruction/docs/source paths; facts learned and any unresolved assumptions.
- Plan/handoffs: PM brief; engineer ownership; specialist trigger and assignment (or why not needed).
- Tools/access: tools actually used; repository vs session configuration; external writes and any observed permission decision.
- AI work: changes, decisions, meaningful corrections/rejected proposals; files and commit when available.
- AI review: reviewer role, criteria/findings, fix/recheck outcome; distinguish source review from runtime checks.
- Human review: reviewer/date/decision and requested changes, or pending/not recorded.
- Verification: exact command or inspection, environment/scope, observed result and safe evidence; list skipped checks with reasons.
- Automation: which checks ran automatically, or none; do not count manual commands as hooks/CI.
- Outcome: completion/limitations, deliverable revision, and follow-up work if any.
```

Keep task prompts and supplied acceptance criteria intact when linking to an
issue or transcript. Do not claim a person reviewed work based on an AI agent
review. Do not say tests passed unless the command was run and its result was
observed. Record deployment evidence only when an actual environment was
deployed and checked.

## Task records

### 2026-10-26 — Close remaining rubric evidence gaps except deployment

- **Task/prompt (summary):** User asked to fix the remaining 1/2 rubric areas:
  AI workflow, API contract, CI/CD, agent extension pack, security/audit/DevOps
  hardening, and observability. Deployment was explicitly excluded.
- **Baseline/scope:** Started from `676c00a` on `main`. Preserved a pre-existing
  unrelated edit in `_docs/team/software-engineer.md`. Did not modify Cloudflare
  deployment files or perform deployment.
- **Context:** Read project instructions, process and testing guidance, rubric
  assessment thread, active OpenAPI/client/Django routes and serializers,
  security-audit skill guidance, existing audit/observability docs, and CI config.
  Independent source reviews compared the API contract with implementation and
  reviewed auth, ownership, browser token handling, telemetry, and extension
  boundaries.
- **AI work:** Corrected OpenAPI descriptions and auth validation wording; added
  the public health contract, nullable/blank schema details, and the date/error
  behavior actually implemented. Added a reusable API-review capability,
  specialist instructions, read-only MCP context server, staged-secret guardrail,
  permission notes, AI data policy, and extension-pack setup guide. CI now
  captures Python/Bun dependency audit output and runs the tracked-content
  guardrail. Added a second source-review report with hardening notes and the
  observed telemetry-start blocker.
- **AI review:** API contract review found no other path/method mismatch after
  the corrections. Security source review found no confirmed exploitable
  vulnerability; public auth throttling and password-validator usage remain
  hardening notes. These were source reviews, not human approval or runtime
  attack tests.
- **Human review:** Not recorded. A project owner still needs to inspect the
  concrete change and provide a decision before this criterion can be claimed.
- **Verification:** Python compilation for the MCP server and secret guardrail
  passed; OpenAPI YAML parsed; the tracked-content guardrail passed on 194
  tracked files; audit findings JSON schema validation passed with zero
  confirmed findings; `git diff --check` passed. The GitHub connector returned
  no status checks or workflow runs for the baseline commit. Docker CLI 29.9.2
  could not connect to `npipe:////./pipe/docker_engine` (`permission denied`),
  so the telemetry stack and Grafana correlation walkthrough were not run.
  Bun was unavailable locally; the Python audit attempt could not access the
  configured uv cache, and `pip-audit` is not installed in the project venv.
- **Automation:** CI workflow definitions include dependency scans and content
  guardrail, but no hosted run for this change exists yet. Audit findings are
  uploaded for triage; the known historical frontend advisories remain an
  unresolved dependency backlog pending a current scan.
- **Outcome:** Source-level workflow, API, extension, and security evidence gaps
  are addressed. Human review, a green hosted Actions run, current lockfile scan
  results, and a correlated Grafana journey remain unverified. Deployment work
  was excluded as requested.

### 2026-10-26 — Close containerization, integration, and CI/CD rubric gaps

- **Task/prompt (summary):** User asked to work on three rubric items: full-app
  containerization, clearly separated integration testing, and CI/CD; the user
  approved preparing Cloudflare CD. No GitHub issue was supplied.
- **Baseline/scope:** Started from `b02cbe7` on `main`. The full Docker Compose
  stack was already committed and had been exercised in the prior task: PostgreSQL,
  Django, and the production-built frontend started healthy, and register/review
  API flows plus browser-facing endpoints were smoke-checked. Other uncommitted
  observability/security-review work was present in the shared tree and is outside
  this rubric change.
- **Acceptance criteria:** Compose supports the whole app; Django/PostgreSQL API
  integration coverage is tagged, separately runnable, and documented; PR/main
  CI checks backend, frontend, and container builds; Cloudflare deployment is
  prepared behind explicit account/configuration gates and is not described as
  deployed without evidence.
- **Plan/handoffs:** PM groomed acceptance criteria. Engineer ownership covered
  integration tagging/docs/CI and the isolated Cloudflare Worker workflow. The
  Cloudflare Python Worker project was kept separate from root dependencies.
  QA's first run hit the account usage limit; a second independent QA review
  completed. Human review is not recorded.
- **AI work:** Django endpoint/database tests now carry the `integration` tag,
  with root README and testing guidance documenting both tagged and non-tagged
  commands and distinguishing the transitional FastAPI compatibility suite.
  `.github/workflows/ci.yml` defines separate Django unit and PostgreSQL
  integration jobs, frontend test/lint/build, and Compose/image builds. An
  optional dependency-audit job was removed after QA reported 25 existing
  frontend advisories; CI does not run dependency advisory scans. A conditional
  Cloudflare workflow, isolated Worker project,
  Hyperdrive binding, frontend Wrangler config, and deployment runbook prepare
  release automation. Hyperdrive's Worker-to-binding socket is distinguished
  from TLS to its PostgreSQL origin; ordinary production PostgreSQL continues
  to require TLS. A dedicated Cloudflare `uv.lock` makes those dependencies
  reproducible. Frontend formatting failures discovered by QA were corrected
  without behavior changes. Architecture wording was updated to match the files.
- **AI review:** Independent QA passed containerization, integration test
  separation, local CI checks, and the Cloudflare preparation scope. It found
  25 frontend dependency advisories when the optional Bun audit was tried. The
  audit job was removed rather than expanding this work into dependency
  upgrades; CI does not claim to scan advisories.
- **Verification:** `uv run python backend/manage.py test --exclude-tag=integration`
  passed 29 tests; `uv run python backend/manage.py test --tag=integration`
  passed 33 tests using the PostgreSQL test database. `docker compose config -q
  && docker compose build && docker compose ps` passed; the already-running
  `db`, `backend`, and `frontend` services were healthy. The API health request
  returned `{"status":"ok"}` and the frontend root returned HTTP 200. In the
  Bun 1.4.4 image, `bun run test` passed 32 tests and `bun run lint` exited 0
  with seven existing Fast Refresh warnings. Both workflow YAML files parsed.
  `uv lock --check --project backend/cloudflare`, Python `compileall` for the
  Worker and packaging script, and `uv run --locked --project backend/cloudflare
  pywrangler --help` passed. `git diff --check` passed. Python `pip-audit`
  reported no known vulnerabilities; Bun audit reported 25 frontend advisories
  before its optional workflow job was removed. No GitHub Actions run, Cloudflare
  build/dry run, account deployment, or managed database check was observed.
- **Outcome:** Rubric implementation passed local QA. Cloudflare account
  resources, GitHub secrets/variables, Worker build compatibility, and deployed
  checks remain unverified. No production deployment is claimed.

### 2026-10-26 — Refresh architecture and AI workflow evidence

- **Task/prompt:** User-directed request in the active Codex conversation to
  correct the stale architecture description and add practical evidence for
  AI-assisted development. The request explicitly prohibited fabricated
  historical prompts, reviews, test runs, or deployment evidence and asked for
  no tests. No GitHub issue was supplied.
- **Acceptance criteria:** Describe the current frontend, Django API,
  PostgreSQL persistence, tests/contracts, transitional code, and the planned
  versus implemented deployment state; document a useful evidence format for
  prompts/tasks, context, human review, and verification.
- **Context read:** Root `AGENTS.md`; `_docs/process.md`, architecture,
  deployment, task-template and role guidance; README files; frontend service
  and auth source; Django settings, routes, models, views, providers, and test
  files; Compose and package configuration.
- **AI work:** PM grooming was supplied in this task conversation. The engineer
  inspected implementation and test sources; after interruptions, the
  orchestrator supplied the initial documentation draft. The engineer reviewed
  and corrected that draft against source, including test-suite boundaries,
  Monday validation, provider modes, legacy contract prose, and the existing
  frontend Cloudflare build hint. The engineer also inspected concurrent local
  Compose/Dockerfile additions and documented their current working-tree state
  without claiming a successful container build or deployment. Changed files:
  `_docs/architecture.md`, `_docs/process.md`, this file, and README
  navigation/test-suite wording. This records the actual handoff rather than
  claiming the prescribed role sequence was followed without deviation.
- **Human review:** Pending. The PM, engineer, and QA role descriptions in
  this repository are AI workflow roles and do not establish human review.
- **Verification:** Tests and builds were not run, as explicitly requested.
  Independent AI QA returned PASS. `git diff --check` exited 0 (Git emitted
  line-ending notices only); the local Markdown link check examined 62 targets
  across the changed documentation and README, with no missing links. No
  deployment was performed or verified.
- **Outcome:** Documentation review complete; human review remains pending.

### 2026-10-26 — Make the AI workflow reusable and explicit

- **Task/prompt (summary):** Expand the AI-development documentation with a
  reusable end-to-end workflow, specialist routing including privacy/security,
  a tool/MCP inventory, permission/guardrail notes, and a practical task record.
  Separate checked-in policy, observed session tools, recommendations, and
  enforced automation. Do not install hooks/tools, add or run tests, or change
  the UI. No GitHub issue was supplied for this documentation work.
- **Baseline/scope:** Started from clean revision `7d2f5bf`. Acceptance criteria:
  the workflow explains intake through delivery; specialist triggers and
  outputs are explicit; tool/configuration claims cite their evidence level;
  records cover prompts, context, role and human reviews, verification, and
  permissions; the prior record remains intact.
- **Context:** Read `AGENTS.md`, this workflow, `process.md`, all three role
  pages, `task-template.md`, and `testing-guidelines.md`. Inspected Git status,
  the starting revision, and tracked paths for MCP/agent configuration, hooks,
  and CI. No such tracked configuration was found at the baseline; application
  settings and React hooks are unrelated to agent permissions or Git hooks.
  Later inspected the concurrent, untracked `.github/workflows/ci.yml` definition
  to distinguish it from committed or executed automation. Its jobs were not
  validated or run as part of this documentation task, and the file was left
  unchanged.
- **Plan/handoffs:** PM-groomed scope was handed to the engineer in the current
  task conversation. The engineer owns the two workflow documents. No separate
  security specialist was needed for this documentation-only change; routing
  guidance defines when future implementation work needs that review.
- **Tools/access:** Used FastCtx MCP to read local files, FastCtx `run` for Git
  and documentation checks, patch editing for the changes, and role
  coordination for handoffs. These were session-provided capabilities. No
  external issue write, tool installation, or permission configuration change
  was performed.
- **AI work:** Expanded `process.md` with bounded handoffs, specialist routing,
  scoped verification, and delivery/closure rules. Expanded this document with
  the evidence inventory, guardrail/enforcement distinctions, and reusable
  record format. Preserved the prior task record.
- **AI review:** Independent QA returned PASS against the documentation criteria.
- **Human review:** Not recorded.
- **Verification:** Source/document inspection completed.
  `git diff --check -- _docs/process.md _docs/ai-development-workflow.md`
  exited 0 with line-ending notices only. An agent-invoked Python check of local
  Markdown link targets passed with no missing paths. Tests and builds are
  outside this task's scope and were not run.
- **Automation:** None ran. No hooks, CI, permissions configuration, or MCP
  configuration was added by this change.
- **Outcome:** Documentation review complete; no commit or deployment performed.

### 2026-10-26 — Record latest QA and Cloudflare proof-of-concept status

- **Task/prompt (summary):** Incorporate the supplied newer QA results into the
  architecture and workflow evidence. Reflect the current Cloudflare Worker
  configs and gated deployment workflow without claiming a live deployment.
  Do not run more tests unless requested.
- **Baseline/scope:** Revision `b02cbe7`; the working tree already contained
  concurrent application, test, observability, and Cloudflare changes. Limit
  this task to `_docs/architecture.md` and this evidence file.
- **Context:** Inspected the current architecture, Cloudflare runbook, CI and
  deployment workflow definitions, frontend Wrangler config, isolated Django
  Worker adapter, and Hyperdrive config. Some new deployment files were
  untracked in the working tree. No Cloudflare account credentials were
  supplied or used.
- **QA evidence supplied:** On 2026-10-26, the shared QA update reports
  `uv run python backend/manage.py test backend.config` passed 20 tests,
  including PostgreSQL SSL mode behavior. It reports frontend lint with 0
  errors and 7 existing `react-refresh` warnings. Earlier shared QA notes also
  report a passing full-app Compose run and Django unit/integration/frontend
  tests; those notes supplied no run IDs, revisions, exact commands, or result
  counts. For the newer results, no run URL/ID, exact revision, or test
  environment was supplied; the lint command was also not named. These are
  attributed reports, not commands run in this task.
- **Configuration evidence:** The current working tree's deployment workflow
  waits for successful CI on `main`, requires `CLOUDFLARE_DEPLOY_ENABLED=true`
  plus account-specific secrets/variables, deploys API and frontend Workers,
  and configures HTTP health/root smoke checks. The workflow has not run. There
  is no evidence of a live Worker, managed database, deployed smoke test, or
  Cloudflare runtime compatibility.
- **Plan/handoffs:** PM grooming was supplied in this task conversation. The
  engineer inspected the current deployment artifacts but hit an agent usage
  limit before editing; the orchestrator updated the two scoped documents.
  Independent documentation QA returned PASS. Human review is not recorded.
- **Tools/access:** Used FastCtx MCP to inspect files and FastCtx `run` to read
  Git status/history. No Cloudflare credentials were accessed; no deployment,
  test, build, or external write was performed.
- **AI work:** Updated this architecture's CI/deployment and test-evidence
  sections and added this source-attributed task record. No application or
  configuration files were changed.
- **Verification:** Independent documentation QA returned PASS. `git diff --check`
  passed for both scoped docs; 68 local Markdown targets resolved. Tests and
  builds were not run, following the instruction in the supplied QA update.
- **Automation:** No CI or deployment workflow was triggered by this task.
- **Outcome:** Documentation update complete; live deployment remains
  unverified.

### 2026-10-26 — Spring cleanup and predeployment security audit

- **Task/prompt (summary):** User requested removing unnecessary files and a
  thorough security-audit skill review of the whole local repository and GitHub
  before deployment. No issue was supplied; no deployment was authorized.
- **Baseline/scope:** Clean tree at `b7c0ae9`, matching remote main. Audit output
  follows the existing `_docs/security-audit/run-3/` convention. Previous two
  source reviews were read, with their historical evidence kept intact.
- **Acceptance criteria:** Remove only demonstrably obsolete/generated content;
  preserve supported behavior; map all trust/input surfaces; validate concrete
  security claims independently; inspect actual GitHub controls/scan evidence;
  deliver reconciled prose and schema-valid JSON; run appropriate checks and
  commit locally. No dependency additions/upgrades or external writes.
- **Plan/handoffs:** PM/recon, three hunters, an independent candidate validator,
  cleanup engineer and independent QA supplied bounded results. Audit agents
  wrote no files. Primary assembled artifacts and fetched/ran evidence checks,
  a documented deviation from pure orchestration to honor the audit skill's
  artifact-ownership rule. This record was assembled after verification; the
  conversation retains intake/handoff timing. Human review is not recorded.
- **AI work:** Retired FastAPI prototype/compatibility tests, removed unreachable
  frontend controls/hook, pruned 14 unused Python lock entries, updated current
  docs and cleared generated caches. Cleanup commit: `f56a513`. Preserved active
  tests/mocks, Uvicorn, migrations, historical evidence and frontend lockfile.
- **Verification:** 29 Django unit tests and 32 frontend tests passed; lint had
  zero errors/two existing warnings; production frontend build and lock check
  passed. Independent synthetic SQLite run passed 61 tests; PostgreSQL-only
  journey excluded. Initial audit harness attempt had four harness-related
  failures, corrected without changing product/tests. Fresh root/Cloudflare
  Python scans reported no known vulnerabilities. Historical blob-pattern scan
  checked 21 reachable commits/273 blobs, no matches. Full evidence/limitations
  are in [run 3 verification](security-audit/run-3/evidence/verification.md).
- **Security review:** No confirmed application exploit survived validation.
  Startup checks, advisory/release gates and GitHub protections remain release
  concerns. Actual hosted frontend scan has 25 advisory entries across nine
  package names/18 advisory URLs, including one critical database rating; no
  application RCE claim is made from that count. Main unprotected, scanners
  disabled, deployment skipped. Two rejected claims and the prose were
  independently checked; findings schema validation passed.
- **Tools/access:** FastCtx file inspection; explicit-workdir built-in commands
  because FastCtx shell did not reach this repository; GitHub connector and
  read-only CLI fallback for unsupported settings. Docker named-pipe access
  failed, so no fresh PostgreSQL/container/deployed test. One hunter's final
  turn was service-blocked; no blocked action is claimed as executed.
- **Outcome:** Scoped cleanup/report QA PASS. [Report](security-audit/run-3/REPORT.md)
  recommends holding deployment until listed release gates and actual staging
  checks pass. No push, PR, external post, GitHub setting change or deployment.
