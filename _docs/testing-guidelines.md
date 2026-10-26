# Testing Guidelines

Use tests to verify user-visible behavior and important product rules. Keep tests deterministic, fast, and independent of a live AI provider, network service, or a developer's personal journal data.

## Before adding a test

1. Read the task's acceptance criteria and identify the behavior that needs proof.
2. Check whether an existing test already covers the same behavior.
3. Choose the narrowest useful test level: unit, component, API integration, or end to end.
4. Use the existing test libraries and project scripts. Ask before adding dependencies.

## Frontend tests

The frontend uses Vitest with a `jsdom` environment and Testing Library setup. Tests live beside the code they exercise or under `frontend/src/test/`, and use the `*.test.ts` or `*.test.tsx` naming convention.

Run the suite from the frontend directory:

```sh
cd frontend
bun run test
```

Use these practices:

- Test outcomes a user or caller can observe: saved data, displayed feedback, navigation, validation, and enabled/disabled actions.
- Query rendered UI by accessible role, label, or visible text. Avoid relying on CSS classes, component internals, or fragile DOM structure.
- Test service behavior with an in-memory `KeyValueStore` or another explicit fake. Do not let tests read or write a developer's browser `localStorage`.
- Keep date-dependent tests stable by passing a fixed date or using explicit week-start values. Cover Sunday/Monday boundaries when changing weekly date logic.
- Cover important edge cases such as one review per week, empty commitments, no history for pattern detection, failed lookups, correction/rejection of insights, and deletion of related data.
- Do not make tests call real AI APIs. Inject a deterministic fake with known outputs and assert that user-provided evidence is retained.
- Prefer testing one behavior per test. Use names that state the condition and expected result.
- Clean up mocks, timers, and rendered components after each test when the test setup does not already do so.

The current frontend test command is also listed in the root README. If you change scripts or test configuration, update the documentation in the same change.

## Backend unit and integration tests

The active backend is Django with Django REST Framework. Tests marked with the Django `integration` tag exercise request handling, authentication, Django models, and the PostgreSQL test database through DRF's API client. They are separate from provider/unit tests and from browser end-to-end tests. The integration tests use Django's isolated test database; they never point at the local development database or production data.

From the repository root, install the locked Python dependencies and start PostgreSQL for the integration group:

```sh
uv sync
docker compose up -d db
```

Run the checks that exclude the endpoint integration group:

```sh
uv run python backend/manage.py test --exclude-tag=integration
```

Run the tagged Django/PostgreSQL endpoint integration group by itself:

```sh
uv run python backend/manage.py test --tag=integration
```

Run both groups together with the default suite:

```sh
uv run python backend/manage.py test
```

Backend tests should cover:

- Validation and business rules for review creation, updates, completion, and unique user/week behavior.
- Authentication and authorization, especially that one user cannot read, update, or delete another user's reviews, reports, or commitments.
- Report generation and error handling with a fake AI provider.
- Commitment lookup strictly before the requested week.
- Cascading deletion of reports and commitments, and deletion of all journal data while preserving the account.

Use the test database and factories or explicit fixtures. Never point tests at a developer or production database. Avoid tests that depend on live provider credentials.

The Django integration tag currently covers registration/login and bearer authentication; journal draft persistence and retrieval; per-user access isolation; report completion and evidence; insight correction; commitment lookup across weeks; and review/account-data deletion. Report and follow-up endpoint tests inject deterministic fakes or mock transport so the suite makes no live AI call. The tag is a focused API/database integration group, not a claim of automated OpenAPI conformance or browser testing.

The optional `pytest` compatibility suite exercises only the transitional FastAPI prototype and its in-memory store. It is not the Django/PostgreSQL integration suite. Run it separately:

```sh
uv sync --extra test
uv run pytest
```

## Browser end-to-end tests

Browser end-to-end tests exercise a small number of complete user journeys through the running application. They are distinct from the Django integration group.

At minimum, the complete weekly-loop journey should verify that a user can:

1. Register or log in.
2. Save and reopen a draft for a week.
3. Complete the review and receive a report with evidence from their reflection.
4. Correct or reject an insight and save a commitment.
5. See that commitment during the next week's reflection.
6. Delete a review or all journal data and verify the related records are gone.

Use isolated test accounts and data. Do not make the tests depend on existing production records, exact AI wording, or timing-sensitive sleeps; wait for an observable state instead.

## Continuous integration

The GitHub Actions workflow in `.github/workflows/ci.yml` runs the Django non-integration group and the tagged PostgreSQL integration group separately, then runs frontend tests, lint, and build. It also validates Compose and builds the backend and frontend images on pull requests and pushes to `main`. A green CI run is evidence for those checks on that revision only; it does not establish deployment or browser end-to-end coverage.

## Test quality and reporting

- A passing test does not replace checking the acceptance criteria. Verify behavior that is not covered by automation manually and record the result.
- When fixing a bug, add a regression test that fails before the fix where practical.
- Do not weaken or delete a test simply to make a suite pass. Update the expected behavior only when the requirement has changed.
- Run the narrowest relevant test while iterating, then run the full relevant suite before reporting completion.
- In the change summary, list the exact commands run and their outcomes. If a command could not be run, say why; do not imply it passed.
