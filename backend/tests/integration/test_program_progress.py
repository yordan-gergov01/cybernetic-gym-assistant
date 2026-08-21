"""`review_program` against a real database.

The rules themselves live in tests/test_plateau.py. What is checked here is the step
those tests cannot see: that the right sets are read out of the log in the first place -
first work set only, no warm-ups - because a verdict built on the wrong sets is wrong
however correct the rule behind it is.
"""
from datetime import date, timedelta

from app.services.program_progress import review_program

from .factories import log_session, make_profile, make_program, make_user, week_days

START = date(2026, 1, 5)

PUSH = ("Push", [("Barbell Bench Press", "chest", 4, 6, 8), ("Triceps Pushdown", "triceps", 3, 10, 15)])


async def sessions(db, user, program, day, benchmarks: list[tuple[float, int]], **kwargs) -> None:
    """One session a week, oldest first, for the exercise the first tuple names."""
    for index, (weight, reps) in enumerate(benchmarks):
        await log_session(
            db, user, program, day, START + timedelta(weeks=index),
            [("Barbell Bench Press", weight, reps)], **kwargs,
        )


async def test_progress_on_every_exercise_extends_the_program(db):
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(db, user, program, day, [(100, 8), (105, 8), (110, 8)])

    review = await review_program(db, program)
    assert review.decision.action == "extend"


async def test_two_sessions_stuck_on_the_same_weight_change_the_exercise(db):
    """The double plateau: the same load twice without an extra rep (p.23)."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(db, user, program, day, [(100, 8), (100, 8), (100, 7)])

    review = await review_program(db, program)
    assert review.decision.action == "adjust_exercise"
    assert review.decision.exercise_name == "Barbell Bench Press"
    assert review.new_rep_target, "the course's first option is a lower rep target"


async def test_one_session_stuck_does_not_touch_the_program(db):
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(db, user, program, day, [(100, 8), (100, 8)])

    review = await review_program(db, program)
    assert review.decision.action == "break_plateau"
    assert [t.name for t in review.techniques if t.exercise_name == "Barbell Bench Press"] == [
        "plateau_breaker"
    ]


async def test_only_the_first_work_set_counts_as_the_benchmark(db):
    """A huge back-off set is not progress; the course benchmarks the first work set."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await log_session(db, user, program, day, START, [("Barbell Bench Press", 100, 8)])
    for week in (1, 2, 3):
        await log_session(
            db, user, program, day, START + timedelta(weeks=week),
            [("Barbell Bench Press", 90, 8), ("Barbell Bench Press", 130, 8)],
        )

    review = await review_program(db, program)
    stalled = [e.exercise_name for e in review.exercises if e.status == "stalled"]
    assert "Barbell Bench Press" in stalled, "the 130 kg second set must not hide the stall"


async def test_warmups_are_not_benchmarks(db):
    """Warm-ups come first in the log; counting them would read every session as a crash."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(
        db, user, program, day, [(100, 8), (105, 8), (110, 8)],
        warmups=[("Barbell Bench Press", 40, 12)],
    )

    review = await review_program(db, program)
    assert review.decision.action == "extend"
    bench = next(e for e in review.exercises if e.exercise_name == "Barbell Bench Press")
    assert bench.status == "progressing"


async def test_an_exercise_with_no_usable_sets_is_reported_not_judged(db):
    """Silence is not a stall - the exercise is named as unassessed instead."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(db, user, program, day, [(100, 8), (105, 8)])

    review = await review_program(db, program)
    assert "Triceps Pushdown" in review.skipped_exercises
    assert all(e.exercise_name != "Triceps Pushdown" for e in review.exercises)


async def test_a_missed_session_gets_a_plateau_breaker_not_a_new_program(db):
    """One session without a new best is answered inside the exercise (p.7)."""
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [PUSH])
    day = (await week_days(db, program, 1))[0]

    await sessions(db, user, program, day, [(100, 8), (105, 8), (102.5, 8)])

    review = await review_program(db, program)
    assert review.decision.action == "extend", "one missed session does not rebuild the program"
    breaker = next(t for t in review.techniques if t.exercise_name == "Barbell Bench Press")
    assert breaker.name == "plateau_breaker"
    assert breaker.how_bg and breaker.source_bg, "the advice has to carry its numbers"
