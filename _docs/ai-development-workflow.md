# AI-assisted development evidence

This log records what repository evidence exists for AI-assisted work. Role
instructions describe the intended workflow; by themselves they do not prove
that a role ran, that a person reviewed a change, or that a check passed.

## Evidence available in this repository

- [`AGENTS.md`](../AGENTS.md) gives project commands and repository rules.
- [`process.md`](process.md) and [`team/`](team/) define PM, engineer, QA, and
  orchestrator responsibilities.
- [`task-template.md`](task-template.md) defines the task brief format.
- [`testing-guidelines.md`](testing-guidelines.md) describes test expectations.
- Git commits record repository changes and commit messages. They do not
  reconstruct prompts, approvals, or test results that were not saved.
- The task record below is the available evidence for this documentation
  change. There is no historical prompt archive or human-review record in the
  repository as of this change.

## Record format

For each substantive task, add a dated entry with enough context to connect the
request to the changed files and checks. A concise record can use this format:

```text
### YYYY-MM-DD — short task name
- Task/prompt: link to issue or transcript; summarize only when the prompt is unavailable.
- Acceptance criteria: link to groomed task or list checkable outcomes.
- Context read: relevant AGENTS.md, process/spec/design/test docs, and source areas.
- AI work: role/agent contributions and changed files; link to commit when one exists.
- Human review: reviewer and outcome, or “pending/not recorded”.
- Verification: exact command/check and observed result, or why it was not run.
- Outcome: complete, incomplete, or follow-up needed.
```

Keep task prompts and supplied acceptance criteria intact when linking to an
issue or transcript. Do not claim a person reviewed work based on an AI agent
review. Do not say tests passed unless the command was run and its result was
observed. Record deployment evidence only when an actual environment was
deployed and checked.

## Current record

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
