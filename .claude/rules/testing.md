# Testing

`python -m pytest` from `backend/`. Config lives in `pyproject.toml`.

## What to test

Priority is the **deterministic engines** — they decide real coaching outcomes and are
pure functions, so they are cheap to test and expensive to get wrong:

- `app/domain/calculators.py` — energy intake, 1RM, volume, goal validation
- `app/services/fatigue.py` — deload decisions
- `app/services/progression.py` — next-session load
- `app/services/weight_trend.py` — trend + calorie adjustment

Do **not** write tests that assert an LLM's exact wording. Grounded-answer quality is
measured separately by `evaluation/offline_eval.py` against the golden dataset.

## Against a database

`tests/integration/` runs on real PostgreSQL — the database named by `TEST_DATABASE_URL`
(default: `DATABASE_URL` + `_test`), which is created on first run and has every table
dropped and rebuilt at the start of a session. Each test lives inside a transaction that
is rolled back, so the services can commit exactly as they do in production. With no
server reachable the package skips with a reason; the pure-function suite still runs.

Put a test here only when the database *is* the thing under test: which rows a query
picks (first work set, no warm-ups), whether a change reaches every week, and who is
allowed to touch what. Rules stay in `domain/` with pure tests — an integration test that
re-checks a threshold is slow duplication.

## How to write them

- **Assert intent, not arithmetic** (CLAUDE.md rule #9). Test that "RIR above target
  means add weight", not that the function returns 102.5. A test that still passes when
  the coaching rule is inverted is worthless.
- Name the behaviour: `test_declining_performance_with_poor_recovery_overrides_threshold`.
- Cover the boundaries that matter: threshold edges, the top of a rep range, missing
  inputs (no RIR logged, too few weigh-ins), and unsorted or noisy input.
- When a test depends on a precondition, assert the precondition too — a threshold test
  should verify the case really is below the threshold before checking the override.
- Import thresholds from the module (`DELOAD_THRESHOLD`) instead of hardcoding numbers,
  so retuning a constant does not silently invalidate the test's meaning.

## Fixtures

Prefer small local builders (e.g. an `answers(**overrides)` helper) over shared fixture
files; each test should read top to bottom without lookups.
