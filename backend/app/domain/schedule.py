"""Which session comes next, and where the user is in the program.

Pure scheduling arithmetic, kept out of the route so it can be tested without a
database or an HTTP layer.

The program model stores days as an ordered sequence (`day_number`), not as weekdays -
nothing records "legs on Tuesday". So the schedule is driven by what has been logged
rather than by the calendar: the next session is the one after the last one performed.
That is also self-correcting, which a fixed weekday map is not - miss Monday and a
calendar-bound plan strands you a day behind for the rest of the block, while this one
simply carries on.

The calendar week is still shown, because "what have I done since Monday" is how people
think about their week; it reports logged days, not planned ones, for the same reason.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

# A working set costs roughly this much on top of its rest interval: the reps
# themselves, plus loading the bar and getting into position. Used only for the
# "~75 мин" estimate on the session card, never for a coaching decision.
WORK_SECONDS_PER_SET = 45
DEFAULT_REST_SECONDS = 120
DEFAULT_SETS = 3


@dataclass(frozen=True)
class CalendarDay:
    date: date
    trained: bool
    is_today: bool


@dataclass(frozen=True)
class SessionEstimate:
    exercise_count: int
    total_sets: int
    minutes: int


def week_number(start_date: date | None, today: date, total_weeks: int) -> int:
    """Which week of the program today falls in, 1-based and clamped to its length."""
    if not start_date or today < start_date:
        return 1
    elapsed = (today - start_date).days // 7 + 1
    return max(1, min(elapsed, max(1, total_weeks)))


def calendar_week(today: date, trained_dates: set[date]) -> list[CalendarDay]:
    """Monday-to-Sunday strip of the current week, marking the days that were trained."""
    monday = today - timedelta(days=today.weekday())
    return [
        CalendarDay(date=day, trained=day in trained_dates, is_today=day == today)
        for day in (monday + timedelta(days=i) for i in range(7))
    ]


def next_day_index(sessions_completed: int, training_day_count: int) -> int | None:
    """Position of the next session in the program's ordered training days.

    Cycles: after the last day of the rotation the next session is the first one again.
    """
    if training_day_count <= 0:
        return None
    return sessions_completed % training_day_count


def estimate_session(exercises: list[dict]) -> SessionEstimate:
    """Rough size of a session, for the card the user reads before starting it.

    An estimate and labelled as one - actual duration depends on how long the person
    rests, which is exactly what the app cannot know in advance.
    """
    total_sets = 0
    seconds = 0
    for exercise in exercises:
        sets = exercise.get("sets_prescribed") or DEFAULT_SETS
        rest = exercise.get("rest_seconds") or DEFAULT_REST_SECONDS
        total_sets += sets
        seconds += sets * (rest + WORK_SECONDS_PER_SET)
    return SessionEstimate(
        exercise_count=len(exercises),
        total_sets=total_sets,
        minutes=round(seconds / 60),
    )


def is_rest_today(*, trained_today: bool, sessions_this_week: int, weekly_target: int) -> bool:
    """Whether today should read as a rest day.

    Two ways to earn one: the session for today is already logged, or the week's planned
    number of sessions is already done. Both are facts about what happened, not a guess
    about what the user intended.
    """
    return trained_today or (weekly_target > 0 and sessions_this_week >= weekly_target)
