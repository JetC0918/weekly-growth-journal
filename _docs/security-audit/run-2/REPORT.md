# Security review — run 2

**Date:** 2026-10-26
**Scope:** PR-style review of the task diff plus active Django authentication and ownership, browser token handling,
telemetry privacy, agent extension boundaries, dependency-scan configuration,
and local operations evidence. Static source review; not deployed.

## Summary

No confirmed exploitable application vulnerability was found in the inspected
source. The auth and ownership protections are source-backed, and the extension
MCP tool is intentionally read-only and path-restricted. This does not establish
runtime security. The previous frontend dependency scan reported 25 advisories
(1 critical, 14 high, 9 moderate, 1 low); the scan's per-package output was not
retained in the repository and could not be rerun in this session because Bun is
unavailable and package network access did not complete. CI now creates an audit
artifact on each run, but no Actions run on the current revision is recorded.

## Findings

No confirmed exploitable vulnerabilities. `findings.json` contains an empty
finding list. This is a source-review result, not a claim that the application
has no vulnerabilities.

## Dependency scan evidence

| Ecosystem | Evidence | Result/status |
| --- | --- | --- |
| Python | Run 1 records `pip-audit` after updating pytest to `9.1.1`. | No known vulnerabilities were reported in that earlier run. The current session's attempt failed before scanning because the configured uv cache could not be opened. |
| Frontend | Run 1 records QA's `bun audit` using Bun 1.4.4. | 25 advisories: 1 critical, 14 high, 9 moderate, 1 low. Package-level output was not saved, so those results are historical evidence, not a current package-by-package finding list. |
| Current CI | `.github/workflows/ci.yml` now runs `pip-audit`, `bun audit --json`, and the tracked-content guardrail, then uploads scan output. | Workflow definition inspected; no hosted run or artifact exists for this revision yet. Audit command failures are retained as artifacts while the known advisory backlog is triaged. |

## Operational diagnosis

Docker CLI 29.9.2 is present, but `docker version` could not connect to
`npipe:////./pipe/docker_engine` and returned `permission denied`. The local
OpenTelemetry stack could not be started from this session. The observed output
does not distinguish a stopped Docker Desktop service from a named-pipe access
restriction. No correlated user journey was collected or viewed in Grafana.

## Hardening notes

- Public registration and login have no application-level throttling. Add an
  edge limit before exposing the API publicly.
- Django password validators are configured, but registration currently calls
  `create_user` without invoking `validate_password`; decide whether the
  configured validators are meant to govern registration.
- Configure secret scanning in the hosting platform as an additional control;
  the repository guardrail uses high-confidence patterns and can miss secrets.
- Recheck Python and JavaScript advisories using the current lockfiles and retain
  machine-readable scan output for each reviewed revision.
- Verify telemetry path scrubbing, collection, retention, and access controls in
  a running stack before enabling production exports.

## Positive patterns

- DRF defaults protected endpoints to signed bearer authentication and
  `IsAuthenticated`; public auth views opt out explicitly.
- Token signatures use HMAC-SHA256 and constant-time comparison with a 24-hour
  expiry.
- Journal queries and full-data deletion are scoped to the authenticated user.
- Browser access tokens stay in module memory and are cleared on expiry or API
  authentication failure.
- Telemetry event names and outcomes are bounded, and the inspected event
  records do not include identifiers or reflection text.
- The MCP server exposes only a fixed allowlist of non-secret documents and has
  no command, network, or write tool.

## Coverage limits

No live API attacks, dynamic browser checks, Docker stack walkthrough, or
deployed access-control review were performed. CI scan configuration was added
but has not yet run. Static source review does not substitute for operational
verification.
