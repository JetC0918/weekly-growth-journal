# Candidate validation detail — run 4

No confirmed MEDIUM-or-higher vulnerability survived validation. No exploitable app finding is omitted from the main report.

## Rejected: stale browser responses disclose another account's report
Input sequence: synthetic account A loads a report; navigate to Account/sign out; clear query state; sign in B; resolve a delayed A callback; revisit the old report route.
- Callback can restore only the old report entry: frontend/src/routes/report.$reviewId.tsx:65–66.
- frontend/src/lib/session-cache.ts:11–15 clears queries, whose installed QueryClient implementation destroys/cancels ordinary in-flight work.
- The loader at report.$reviewId.tsx:32–38 still fetches the owned review and optional commitment. backend/journal/views.py:68 scopes the review by authenticated user; GET at :124–127 returns JSON null200 for wrong ownership.
- The loader rejects null with notFound and the component at :61 requires review+report before rendering. Browser-conditioned route testing and the independent exact-null guard test blocked display.
- Independent result: old ordinary query CancelledError, B-only cache; explicit stale report remained only as an unreachable cache entry, review=null, loaderThrowsNotFound=true, reportPageCanRender=false.
The initial hunter's mock returned404, stricter than the actual null200 response. The independent null-response test resolved that factual discrepancy.

A different stale401 sequence does expire current B. That behavior was independently reproduced with actual TypeScript transpiled in memory and fake fetch, but no remote attacker-controlled execution path, credential acquisition or cross-account operation was established. It is a session-generation hardening note, not the claimed report disclosure.

## Rejected: username representation produces victim account takeover/denial
Exact synthetic inputs:
- POST /api/auth/register with JSON username 31415.9265 and password "31415.9265":201; string username "31415.9265" with same password:422.
- Register "audituser" and then "\U0001d400udituser" (mathematical bold capital A), with distinct test passwords:201/201; stored names audituser/Audituser.
The raw username reaches Django's password-similarity user attribute at backend/accounts/serializers.py:40–43. Installed DRF CharField coerces numeric values to strings; Django's similarity validator skips non-string user attributes. Separately views.py:24 casefolds before create_user's NFKC normalization. Login at views.py:63–68 finds the first case-insensitive match and still verifies its password; installed QuerySet.first orders by PK if unordered.
Independent result: distinct token subjects, victim login200 with unchanged subject, second login401, second bearer saw zero victim reviews, victim review remained present. The effect is a policy bypass/self-account login failure, not victim takeover or an ownership bypass.

## Other focused checks
The business-logic hunter used fake-provider interleavings with SQLite :memory:. Owned history entered AI context; foreign commitment ID was stripped by backend/feedback/reports.py:30–47. Editing while generating stored an older report snapshot; deleting while generating returned generic500 without resurrection or victim mutation. These are documented reliability notes; deterministic interleavings are not PostgreSQL race testing.

## Deployment observations are not exploit findings
The configured Worker endpoints returned Hello World! and the origin validator rejects the trailing slash in both stored variables. These are reproduced release-readiness failures. HTTP200 on a placeholder is not evidence of an auth bypass or a functioning journal API. No live authenticated attack was attempted.
