"""Applying a verdict, against a real database.

The point of every test here is the same: a change has to reach **every** week. The
training rotation is served from the first week, so a change that lands on one week only
is a change the user never sees - and one that lands on later weeks only never happens
at all.
"""
from sqlalchemy import select

from app.domain.exercise_library import find
from app.models import WorkoutSet
from app.domain.program_design import plan_muscle_adjustment
from app.services.program_adjust import (
    apply_muscle_adjustment,
    apply_rep_range,
    apply_swap,
    exercise_rows,
    program_weeks,
    template_days,
)

from .factories import log_session, make_profile, make_program, make_user, prescribed, week_days

UPPER = ("Upper", [("Barbell Bench Press", "chest", 4, 6, 8), ("Cable Fly", "chest", 3, 10, 15)])
LOWER = ("Lower", [("Barbell Squat", "quads", 4, 6, 8)])

WEEKS = 4


async def test_a_swap_reaches_every_week(db):
    user = await make_user(db)
    program = await make_program(db, user, [UPPER, LOWER], weeks=WEEKS)
    weeks = await program_weeks(db, program.id)
    replacement = find("Arnold Press")

    change = await apply_swap(db, exercise_rows(weeks, "Barbell Bench Press"), replacement)

    assert change.rows_changed == WEEKS
    assert not await prescribed(db, program, "Barbell Bench Press")
    assert len(await prescribed(db, program, "Arnold Press")) == WEEKS


async def test_a_swap_carries_the_muscle_group_of_the_new_exercise(db):
    user = await make_user(db)
    program = await make_program(db, user, [UPPER, LOWER], weeks=2)
    weeks = await program_weeks(db, program.id)

    await apply_swap(db, exercise_rows(weeks, "Barbell Bench Press"), find("Arnold Press"))

    rows = await prescribed(db, program, "Arnold Press")
    assert {row.muscle_group for row in rows} == {"shoulders"}, "an overhead press is not chest work"


async def test_a_swap_drops_the_load_target_of_the_exercise_it_replaced(db):
    """The target is the next session's weight for the old lift; on a new movement it
    would prescribe a weight nobody has ever handled there."""
    user = await make_user(db)
    program = await make_program(db, user, [UPPER, LOWER], weeks=2)
    for row in await prescribed(db, program, "Barbell Bench Press"):
        row.target_weight_kg = 102.5
        row.target_reps = 8
    await db.flush()

    weeks = await program_weeks(db, program.id)
    await apply_swap(db, exercise_rows(weeks, "Barbell Bench Press"), find("Arnold Press"))

    assert all(row.target_weight_kg is None for row in await prescribed(db, program, "Arnold Press"))


async def test_a_swap_does_not_rewrite_what_was_already_lifted(db):
    """The log is history: it says what was done, not what is planned."""
    user = await make_user(db)
    program = await make_program(db, user, [UPPER, LOWER], weeks=2)
    days = await week_days(db, program, 1)
    logged = await log_session(
        db, user, program, days[0], program.start_date, [("Barbell Bench Press", 100, 8)]
    )

    weeks = await program_weeks(db, program.id)
    await apply_swap(db, exercise_rows(weeks, "Barbell Bench Press"), find("Arnold Press"))

    r = await db.execute(select(WorkoutSet).where(WorkoutSet.workout_log_id == logged.id))
    assert [s.exercise_name for s in r.scalars().all()] == ["Barbell Bench Press"]


async def test_intensification_reaches_every_week(db):
    user = await make_user(db)
    program = await make_program(db, user, [UPPER, LOWER], weeks=WEEKS)
    weeks = await program_weeks(db, program.id)

    await apply_rep_range(db, exercise_rows(weeks, "Cable Fly"), (6, 11))

    rows = await prescribed(db, program, "Cable Fly")
    assert len(rows) == WEEKS
    assert {(row.reps_min, row.reps_max) for row in rows} == {(6, 11)}


async def test_raising_frequency_moves_the_exercise_in_every_week(db):
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [UPPER, LOWER], weeks=WEEKS)
    weeks = await program_weeks(db, program.id)

    adjustment = plan_muscle_adjustment(template_days(weeks), "chest", target_weekly_sets=16)
    change = await apply_muscle_adjustment(db, weeks, adjustment)

    assert change.action == "move_exercise"
    assert change.rows_changed == WEEKS
    for week_number in range(1, WEEKS + 1):
        days = await week_days(db, program, week_number)
        chest_days = [d for d in days if any(e.muscle_group == "chest" for e in d.exercises)]
        assert len(chest_days) == 2, f"week {week_number} still trains chest only once"


async def test_raising_frequency_keeps_the_weekly_sets_where_they_were(db):
    user = await make_user(db)
    await make_profile(db, user)
    program = await make_program(db, user, [UPPER, LOWER], weeks=2)
    weeks = await program_weeks(db, program.id)

    def chest_sets(days) -> int:
        return sum(e.sets_prescribed for d in days for e in d.exercises if e.muscle_group == "chest")

    before = chest_sets(await week_days(db, program, 1))
    adjustment = plan_muscle_adjustment(template_days(weeks), "chest", target_weekly_sets=16)
    await apply_muscle_adjustment(db, weeks, adjustment)

    assert chest_sets(await week_days(db, program, 1)) == before


async def test_a_full_week_gets_a_set_instead_of_a_session(db):
    """Every training day already trains chest, so frequency cannot go any higher."""
    user = await make_user(db)
    await make_profile(db, user)
    chest_a = ("A", [("Barbell Bench Press", "chest", 4, 6, 8), ("Cable Fly", "chest", 3, 10, 15)])
    chest_b = ("B", [("Incline Press", "chest", 3, 8, 12)])
    program = await make_program(db, user, [chest_a, chest_b], weeks=WEEKS)
    weeks = await program_weeks(db, program.id)

    adjustment = plan_muscle_adjustment(template_days(weeks), "chest", target_weekly_sets=16)
    change = await apply_muscle_adjustment(db, weeks, adjustment)

    assert change.action == "add_sets"
    assert {row.sets_prescribed for row in await prescribed(db, program, "Barbell Bench Press")} == {5}
