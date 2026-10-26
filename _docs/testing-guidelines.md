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

## Backend tests

The planned backend uses Django. When backend code is added, use Django's test framework and keep tests with the app or in its `tests/` package. Run the project's documented command:

```sh
uv run python manage.py test
```

Backend tests should cover:

- Validation and business rules for review creation, updates, completion, and unique user/week behavior.
- Authentication and authorization, especially that one user cannot read, update, or delete another user's reviews, reports, or commitments.
- Report generation and error handling with a fake AI provider.
- Commitment lookup strictly before the requested week.
- Cascading deletion of reports and commitments, and deletion of all journal data while preserving the account.

Use the test database and factories or explicit fixtures. Never point tests at a developer or production database. Avoid tests that depend on live provider credentials.

## Integration and end-to-end tests

Keep API integration and browser end-to-end tests clearly separate from unit tests. Integration tests should verify the OpenAPI contract against the Django API and PostgreSQL. End-to-end tests should exercise a small number of complete user journeys through the running application.

At minimum, the complete weekly-loop journey should verify that a user can:

1. Register or log in.
2. Save and reopen a draft for a week.
3. Complete the review and receive a report with evidence from their reflection.
4. Correct or reject an insight and save a commitment.
5. See that commitment during the next week's reflection.
6. Delete a review or all journal data and verify the related records are gone.

Use isolated test accounts and data. Do not make the tests depend on existing production records, exact AI wording, or timing-sensitive sleeps; wait for an observable state instead.

## Test quality and reporting

- A passing test does not replace checking the acceptance criteria. Verify behavior that is not covered by automation manually and record the result.
- When fixing a bug, add a regression test that fails before the fix where practical.
- Do not weaken or delete a test simply to make a suite pass. Update the expected behavior only when the requirement has changed.
- Run the narrowest relevant test while iterating, then run the full relevant suite before reporting completion.
- In the change summary, list the exact commands run and their outcomes. If a command could not be run, say why; do not imply it passed.
