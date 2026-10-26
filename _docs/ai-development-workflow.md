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
| Automated hooks/CI | The baseline had no tracked hook, pre-commit, or CI setup. The concurrent untracked CI definition described above is now present in the working tree, but its execution and required-check status are unverified. The diff/link checks in these records were invoked manually by an agent, not by hooks or CI. Do not describe configured checks as enforced until the relevant settings and execution are observed. |

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
