# Agent extension pack

This pack is a small, local-first reference implementation for AI-assisted
changes in this repository. Its boundaries are documented; it does not grant
additional access or imply that an agent runner is installed.

| Area | Artifact | Purpose |
| --- | --- | --- |
| Project instructions | [`../AGENTS.md`](../AGENTS.md) | Commands, documentation, and dependency rules. |
| Reusable capability/workflow | [`../agent-capabilities/openapi-contract-review.md`](../agent-capabilities/openapi-contract-review.md) | Repeatable contract-to-client-to-backend review. |
| Specialist | [`../plugins/weekly-growth-specialists/api-contract-reviewer.md`](../plugins/weekly-growth-specialists/api-contract-reviewer.md) | Bounded API architecture review with source evidence. |
| MCP server | [`../mcp-server/src/server.py`](../mcp-server/src/server.py) | Read-only retrieval of approved project guidance. |
| Hook/guardrail | [`../agent-hooks/pre-commit`](../agent-hooks/pre-commit) and [`../agent-hooks/check_staged_changes.py`](../agent-hooks/check_staged_changes.py) | Blocks likely secrets in staged content; CI can scan tracked files. |
| Permission notes | [`permissions.md`](permissions.md) | Defines file, tool, data, and external-action boundaries. |
| AI data policy | [`ai-tool-data-policy.md`](ai-tool-data-policy.md) | Defines context that may and may not be sent to AI tools. |

## Local setup

Use Python 3.11 or newer. The MCP server uses only the Python standard library.
Configure an MCP host to launch `python mcp-server/src/server.py` from the
repository root using stdio transport. The server exposes only
`get_project_guidance` and accepts one of the fixed document IDs in its input
schema.

To install the optional Git hook for this checkout, run
`git config --local core.hooksPath agent-hooks`. To remove that setting later,
run `git config --local --unset core.hooksPath`. The hook checks staged content
before each commit. CI uses the same scanner against tracked files. The hook is
not active until installed in a checkout.

## Security and limitations

The MCP server has no filesystem argument, command execution, network client,
or write operation. Its allowlist is the only way to select content. The secret
scanner is a preventive heuristic, not a complete secret detector; human review
and secret scanning in the hosting platform remain useful. Do not add private
journal data, credentials, or arbitrary files to the MCP allowlist. See
[`permissions.md`](permissions.md) and [`ai-tool-data-policy.md`](ai-tool-data-policy.md).
