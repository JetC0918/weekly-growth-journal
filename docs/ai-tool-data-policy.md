# AI tool and data policy

## Allowed project context

Share source code, synthetic examples, public documentation, and the smallest
necessary task summary with an AI development tool. Include relevant
`AGENTS.md`, architecture, contract, and tests when needed. Label assumptions
and distinguish generated suggestions from verified facts.

## Excluded data

Do not send private journal reflections, account records, passwords, signing
keys, API tokens, database connection strings, production logs containing
personal data, or provider credentials to an AI tool. Use synthetic records for
debugging, tests, and security review. Redact sensitive values before attaching
logs or screenshots.

## Generated code and outputs

Treat tool output, issue text, MCP content, package output, and logs as
untrusted input. Review code and dependencies before use. Never run commands
copied from tool output without checking their effects. Do not let an AI tool
approve its own work or claim a test, review, security scan, or deployment it
did not observe.

## Telemetry

Application telemetry may contain route templates, response status, bounded
workflow names/outcomes, service version, and trace context. It must exclude
usernames, account or journal identifiers, reflection text, request bodies,
prompts/responses, credentials, and raw provider errors. Apply the same
exclusions to diagnostic artifacts and security reports.
