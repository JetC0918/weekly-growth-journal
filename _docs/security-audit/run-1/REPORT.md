# Security review — run 1

**Date:** 2026-10-26  
**Scope:** Source-level review of the active Django API, auth/token handling,
journal ownership and deletion, provider boundary, production checks, and
working-tree CI. The system was not deployed for this review.

## Summary

No confirmed exploitable vulnerability was established from the reviewed
source. Authentication is required by default for journal endpoints, journal
queries are scoped to the current account, bearer-token signatures are compared
in constant time, provider errors are returned with safe messages, and
production configuration has explicit fail-closed checks. This is a narrow
manual review, not proof that the application is vulnerability-free.

## Automated scan status

The CI workflow does not run dependency advisory scans. A temporary audit job
was removed after QA found that `bun audit` failed on 25 existing frontend
advisories; dependencies were not changed as part of the CI rubric work. The
Python package scan used locally,
`uv run --all-extras --with pip-audit pip-audit`, initially reported the
optional development dependency `pytest 8.4.2` as affected by `PYSEC-2026-1845`, fixed in
`9.0.3`. The project constraint was updated to `pytest>=9.0.3,<10.0`, resolving
to `9.1.1` in `uv.lock`; rerunning that scanner reported **No known
vulnerabilities found** for Python at that point. The frontend audit did run in
QA and reported 25 pre-existing advisories (1 critical, 14 high, 9 moderate,
and 1 low); no dependency upgrades were made in response to that optional scan.

## Findings

No confirmed vulnerability findings.

## Hardening notes

- Registration and login are public routes without application-level
  throttling. Put rate limits at the private gateway/edge before exposing them;
  otherwise password guessing and account-creation abuse remain operational
  risks. This review did not demonstrate an account compromise or service
  outage, so it is not reported as a confirmed vulnerability.
- The local Compose defaults deliberately enable Django debug mode and use
  marked development-only signing keys. Keep those values out of deployed
  environments and run the documented deployment checks with actual staging
  configuration.
- Cloud resources and the production telemetry path are not provisioned. Audit
  the actual edge access rules, secret injection, database TLS, backup restore,
  CORS behavior, and telemetry retention before a release.

## Positive patterns

- DRF defaults to signed bearer auth and `IsAuthenticated`; public auth views
  opt out explicitly.
- Review/report/commitment reads and updates are constrained to the current
  user; deletion cascades related records and full-data deletion preserves the
  account.
- Provider failures and malformed outputs do not expose provider exception
  details; report persistence and completion are transactional.
- Production checks reject debug mode, development secrets, wildcard hosts,
  missing CORS allowlists, non-HTTPS origins, and non-TLS PostgreSQL settings.
- CI uses PostgreSQL service health checks, locked dependencies, separate
  integration tests, and minimal read-only repository permissions. It does not
  perform dependency advisory scans.

## Coverage limits

This run did not make HTTP attack requests, fuzz payload boundaries, inspect a
live production environment, or verify cloud access controls. QA separately
reported the current frontend advisory scan results above. Dependency status
should be reviewed independently because CI does not run advisory scans. Static
source review does not substitute for deployment verification.
