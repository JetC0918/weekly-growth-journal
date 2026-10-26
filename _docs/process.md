# Work process

Work on one GitHub issue at a time, or on the user's supplied task when no
issue exists. Read its acceptance criteria before starting and before closing
it. Commit changes regularly. This is a documented workflow, not an installed
agent runner, permission system, Git hook, or CI pipeline.

## Roles and handoffs

The main session is the orchestrator. It launches PM, engineer, and QA
subagents, supplies each with the task and relevant context, and coordinates
their handoffs. It does not groom, implement, or test itself. Record deviations
honestly rather than rewriting the history to match this process.

| Role | Responsibility and handoff |
| --- | --- |
| [PM](team/pm.md) | Groom the request with [the task template](task-template.md): goal, checkable acceptance criteria, out of scope, and constraints. Hand the brief and source/context links to the engineer. |
| [Engineer](team/software-engineer.md) | Inspect the current implementation, implement the groomed scope, and provide changed files, decisions, checks, and unresolved limitations to QA. Do not close the issue. |
| [QA](team/qa-engineer.md) | Independently check every acceptance criterion and report PASS or FAIL with evidence. Do not fix the implementation. Return failures to the engineer with a reproducible observation. |
| Human task owner/reviewer | Supply requirements and make product or release decisions within the task's scope. Record an actual review separately from AI role reviews; do not infer approval from silence or from an agent's PASS. |

## End-to-end workflow

1. **Capture the request.** Start a dated record using
   [the evidence format](ai-development-workflow.md#record-format). Preserve
   the prompt or a clearly labeled excerpt/summary, source issue or chat, base
   revision, requested outcome, and explicit constraints.
2. **Collect context and groom.** Inspect the working tree and applicable
   `AGENTS.md` files. Read this process, the task, and the relevant source before
   proposing changes. PM writes the acceptance criteria and names any needed
   specialist review. Use [specs](specs.md), [architecture](architecture.md),
   and [OpenAPI](../openapi.yaml) where they inform the work. Read
   [testing guidelines](testing-guidelines.md) before writing tests and the
   [design system](design-system.md) for UI work.
3. **Assign bounded work.** Give the engineer the groomed brief, file ownership,
   context links, and permitted checks. Tell parallel workers that they share
   the repository and must preserve other changes. Do not send whole unrelated
   directories or personal journal data as context.
4. **Implement and record decisions.** The engineer makes the scoped change,
   retains meaningful corrections or rejected approaches in the record, and
   prepares a concrete diff. Follow `AGENTS.md`'s dependency approval rule;
   dependencies, external writes, or destructive actions outside existing
   authorization require resolution before proceeding.
5. **Review where needed.** Use the specialist routing below for changes that
   cross a relevant boundary. A specialist supplies findings and evidence to
   the engineer/QA; it does not replace acceptance review or imply a human
   sign-off.
6. **Verify the result.** QA checks acceptance criteria against source and the
   appropriate observed behavior, following the task's permitted verification
   scope. Record each actual command/check and result. If the user explicitly
   prohibits tests or limits work to documentation, honor that instruction,
   explain skipped checks, and scope the verdict accordingly. Never label an
   unrun check as passed.
7. **Iterate and deliver.** On FAIL, return findings to the engineer, then recheck
   the correction. On PASS, deliver changed files, observed verification,
   remaining limits, and the review status to the user. Record any human
   feedback when received; an unrecorded human review stays unrecorded. This
   record does not add an approval gate to already authorized work.
8. **Commit and close within scope.** Commit the task's changes without
   including unrelated work, link the resulting revision, and update the
   evidence record. Only the orchestrator closes an issue after QA PASS and
   within the authorized task scope. Do not create or post to an external issue
   merely to populate this log. Pick the next backlog issue only when continued
   backlog work is authorized.

## Specialist routing

These are focus areas to assign when applicable, not evidence that permanent
specialist agents or automatic routing are installed. The three role pages
above remain the checked-in role instructions.

| Trigger | Review focus | Useful handoff evidence |
| --- | --- | --- |
| API, model, or frontend/backend boundary changes | Architecture/contract specialist: compare client, OpenAPI, serializers, ownership, transactions, and compatibility. | Affected endpoints/schema, source references, contract mismatches, migration implications. |
| Authentication, journal ownership, deletion/export, logging, AI context, secrets, or deployment access changes | Privacy/security specialist: trace which user data crosses each boundary; inspect authorization, secret handling, retention/deletion, and failure disclosure. | Concrete source-backed findings, affected boundary, reproduction or inspection evidence, and proposed correction. Use synthetic data; do not copy private reflections or credentials into the record. |
| UI behavior or accessibility changes | UI/accessibility specialist using the design system: examine user flows, focus/keyboard behavior, labels, and failure states. | Relevant screens/flows and reproducible observations. |
| Database migration, container/runtime, or release configuration changes | Data/operations specialist: review persistence, compatibility, health checks, recovery, and environment-specific settings. | Configuration diff, migration/rollback plan, and clearly separated local versus deployed evidence. |

For a narrow documentation task, PM may record that no additional specialist
is needed. An architecture or privacy/security review can also be a focused
assignment to an available reviewer; name the actual role and scope used.

## Evidence and permissions

Maintain [the workflow record](ai-development-workflow.md) at intake, handoff,
verification, and delivery. It distinguishes repository policy, observed
session tools, recommended practices, and enforced automation. Record tool
restrictions or approval outcomes only when observed, without secret values.
Existing session authorization carries forward; ask only for missing scope or
authority, or when an actual tool permission gate requires it.
