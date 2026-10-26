# Agent and tool permissions

## Default access

- Read only project files needed for the assigned task.
- Edit only files in the task's stated scope; preserve unrelated working-tree
  changes.
- Use local deterministic checks before requesting or using external services.
- Do not expose account credentials, access tokens, private journal content, or
  provider prompts/responses in prompts, logs, telemetry, artifacts, or commits.

## External and destructive actions

Deployment, database deletion, publishing, sending messages, pushing a branch,
changing repository settings, or creating external resources require explicit
task authorization. Inspect the concrete target and effect first. A local test
database or local Compose volume is not production data, but removing a volume
still requires a clear task need.

## MCP server scope

`mcp-server/src/server.py` exposes only four fixed, read-only guidance documents.
Its tool accepts an enum instead of a path, performs no network access, and
cannot run commands or modify files. Keep private reflections, credentials,
`.env` files, user database records, and arbitrary paths out of its document map.

## Hook and CI scope

`agent-hooks/check_staged_changes.py` reads only staged blobs when used as a
pre-commit hook. CI may scan tracked repository files with `--tracked`. It
blocks likely secret files and high-confidence credential patterns; passing it
does not prove that a repository contains no secrets. Review every match and
avoid printing matched secret values.

## Review boundary

AI review and automated checks are evidence, not human approval. Record a human
review only when the task owner or another identified person supplies a date,
decision, and any requested changes.
