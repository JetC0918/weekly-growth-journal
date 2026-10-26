# Work process

- Work on one GitHub issue at a time.
- Read the issue’s acceptance criteria before starting and before closing it.
- Commit changes regularly.
- For substantive AI-assisted work, keep a concise evidence record using
  [`ai-development-workflow.md`](ai-development-workflow.md). Create or update
  it when the task is groomed, then record implementation, review, and
  verification outcomes as they actually occur. Do not backfill missing
  historical prompts, approvals, test results, or deployment evidence.


Roles

- PM - grooms a task before anyone implements it, follows _docs/team/pm.md
-  Engineer - implements one groomed task, follows _docs/team/software-engineer.md
- QA - checks the result against the acceptance criteria, follows _docs/team/qa-engineer.md

Orchestrator

The main session is the orchestrator. It launches the PM, the engineer
and QA as subagents. It does not groom, implement or test itself.

Lifecycle

1. Pick the next open issue from the backlog
2. PM grooms it
3. Engineer implements it
4. QA verifies it
5. On FAIL, back to step 3 with the QA comment as input
6. On PASS, close the issue
7. Repeat until the backlog is empty

For work without a GitHub issue, record the supplied task and acceptance
criteria in the local workflow evidence log. AI role reviews and agent reports
are separate from human review; label each accurately.

Rules

- Do not skip step 2
- The engineer does not close the issue
- QA does not fix the code, only outputs PASS or FAIL
- The orchestrator closes the issue only after QA outputs PASS
