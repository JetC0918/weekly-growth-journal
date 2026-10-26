# Capability: Review the API contract

Use this workflow when an API route, request, response, or client call changes.

## Inputs

- The user-visible request and acceptance criteria.
- `openapi.yaml` as the HTTP contract.
- The active frontend service under `frontend/src/services/`.
- Django routes, views, serializers, authentication, and exception handling.

## Steps

1. Identify the active frontend service and all request paths, methods, headers,
   payloads, expected statuses, and response shapes for the changed behavior.
2. Trace each request into Django's URL configuration, view, serializer, and
   exception handler. Include auth defaults, ownership scope, and transaction
   behavior where they affect outcomes.
3. Compare those facts with every matching OpenAPI operation and schema.
   Document actual nullable/blank behavior, error statuses, and date rules.
4. Update implementation and contract together when the requested product rule
   requires a behavior change. Otherwise, correct the contract to match the
   observed implementation and identify transitional code separately.
5. Run the narrowest relevant checks; record exact commands and outcomes. A
   schema being parseable does not establish runtime conformance.

## Output

Return a table of endpoint, source behavior, contract behavior, correction, and
verification. Report unknowns as unknown. Never infer a successful live request
from source inspection alone.
