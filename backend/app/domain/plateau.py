"""Deterministic plateau detection and program-continuation rules (Henselmans).

Whether a program should keep running is a measurement, not a judgment call: the same
log must always yield the same verdict, which rules out asking a model. Every threshold
below is taken from the course material; the two places where the course gives a
principle rather than a number are marked as such.

Sources, with the page of the extracted PDF:

- Progression Guidelines, p.3 - the FIRST work set is the benchmark of progress for an
  exercise; later sets do not count towards it.
- Progression Guidelines, p.7 - plateau breaker: after a session without progress, add
  ~10% next session, capped at roughly a 3RM (compound) or 5RM (isolation), then drop
  back an increment and work the reps up again.
- Periodization & progress, p.44 - taking every 4th week off is "proactive but
  arbitrary"; the timing of overreaching cannot be predicted in advance. This is why a
  program that is still producing progress is extended rather than ended on a date.
- Periodization & progress, p.45 - a reactive deload is warranted when strength does not
  progress by 2.5% on an exercise, or when reps come out lower instead of higher than
  last time. Advanced trainees use 1%, since they can no longer expect 2.5% consistently.
- Periodization & progress, p.23-25 - a single plateau has many possible causes; a
  DOUBLE plateau at the same strength level is cause to change the program. First decide
  whether the plateau is systemic (several exercises for unrelated muscle groups) or
  local (one muscle group, or one exercise), because the fix differs.
- Periodization & progress, p.24 - for a single stalled exercise, intensify by lowering
  the rep target by at least 4 points, never below 4 reps per set; if that is not
  possible, replace the exercise.
- Periodization & progress, p.61 - gaining strength excludes overtraining by definition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.calculators import calculate_1rm

# thresholds from the course

MIN_PROGRESS_PCT = 2.5      
ADVANCED_MIN_PROGRESS_PCT = 1.0  
ADVANCED_TRAINING_STATUS = 3

PLATEAU_BREAKER_PCT = 10.0   
BREAKER_CAP_REPS_COMPOUND = 3  
BREAKER_CAP_REPS_ISOLATION = 5 

REP_TARGET_INTENSIFICATION = 4 
MIN_REPS_PER_SET = 4  

# The course says a DOUBLE plateau justifies changing the program (p.23) but does not
# put a session count on it. The plateau-breaker cycle of p.7 is attempt -> breaker ->
# attempt, so three sessions without a new best is the smallest window in which two
# genuine attempts have failed.
STALL_SESSIONS = 3

# The course calls a plateau systemic when it spans "unrelated" muscle groups (p.23)
# without defining relatedness. Muscles trained together in one movement pattern are
# treated as related, so a stalling bench press and triceps extension read as one local
# problem rather than a whole-body recovery failure.
_MUSCLE_REGION = {
    "chest": "push", "shoulders": "push", "triceps": "push", "front_delts": "push",
    "back": "pull", "lats": "pull", "biceps": "pull", "rear_delts": "pull",
    "forearms": "pull", "traps": "pull",
    "quads": "legs", "hamstrings": "legs", "glutes": "legs", "calves": "legs",
    "abs": "core",
}

# Product decision, not a course rule: a program is never carried past this, so a
# stale plan cannot run forever unnoticed.
MAX_PROGRAM_WEEKS = 20


@dataclass(frozen=True)
class BenchmarkSet:
    """The first work set of one session - the course's progress benchmark (p.3)."""

    date: date
    weight_kg: float
    reps: int

    @property
    def e1rm(self) -> float:
        """Strength expressed as one number, so weight and reps are comparable."""
        return calculate_1rm(self.weight_kg, self.reps).estimated_1rm


@dataclass(frozen=True)
class SessionChange:
    """How the latest session compares with the one before it, for one exercise."""

    change_pct: float
    reps_dropped: bool
    progressed: bool
    needs_reactive_deload: bool


@dataclass(frozen=True)
class ExerciseProgress:
    exercise_name: str
    muscle_group: str | None
    status: str # progressing | holding | stalled | insufficient_data
    sessions_since_best: int
    best_e1rm: float | None = None
    latest_e1rm: float | None = None
    last_session: SessionChange | None = None


@dataclass(frozen=True)
class ProgramDecision:
    """What to do with the program as a whole."""

    action: str # extend | adjust_exercise | adjust_muscle | check_recovery | complete
    scope: str | None # systemic | local_muscle | local_exercise | None
    reason_bg: str
    stalled: list[ExerciseProgress] = field(default_factory=list)
    muscle_group: str | None = None # set for adjust_muscle
    exercise_name: str | None = None # set for adjust_exercise


def min_progress_pct(training_status: int | None) -> float:
    """Advanced trainees cannot hold 2.5% per session, so they are judged at 1% (p.45)."""
    return (
        ADVANCED_MIN_PROGRESS_PCT
        if training_status == ADVANCED_TRAINING_STATUS
        else MIN_PROGRESS_PCT
    )


def compare_sessions(previous: BenchmarkSet, latest: BenchmarkSet, training_status: int | None) -> SessionChange:
    """Judge one session against the previous one for the same exercise.

    Fewer reps than last time triggers a reactive deload on its own (p.45) - it is the
    course's explicit signal, regardless of what the percentage says.
    """
    threshold = min_progress_pct(training_status)
    change_pct = (latest.e1rm / previous.e1rm - 1) * 100 if previous.e1rm else 0.0
    reps_dropped = latest.reps < previous.reps and latest.weight_kg <= previous.weight_kg
    progressed = change_pct >= threshold and not reps_dropped
    return SessionChange(
        change_pct=round(change_pct, 2),
        reps_dropped=reps_dropped,
        progressed=progressed,
        needs_reactive_deload=reps_dropped or change_pct < threshold,
    )


def classify_exercise(
    exercise_name: str,
    muscle_group: str | None,
    sessions: list[BenchmarkSet],
    training_status: int | None = None,
) -> ExerciseProgress:
    """Classify one exercise from its benchmark sets, oldest session first.

    `stalled` means two real attempts to beat the best have failed (see STALL_SESSIONS);
    a single missed session is `holding` and is handled by the plateau breaker inside the
    exercise, not by rebuilding the program (p.23).
    """
    ordered = sorted(sessions, key=lambda s: s.date)
    if len(ordered) < 2:
        return ExerciseProgress(
            exercise_name=exercise_name,
            muscle_group=muscle_group,
            status="insufficient_data",
            sessions_since_best=0,
            latest_e1rm=ordered[0].e1rm if ordered else None,
            best_e1rm=ordered[0].e1rm if ordered else None,
        )

    e1rms = [s.e1rm for s in ordered]
    best = max(e1rms)
    # The LAST session reaching the best counts, so repeating a personal best is not
    # read as drifting away from it.
    best_index = len(e1rms) - 1 - e1rms[::-1].index(best)
    sessions_since_best = len(ordered) - 1 - best_index

    last_session = compare_sessions(ordered[-2], ordered[-1], training_status)

    if sessions_since_best == 0:
        status = "progressing"
    elif sessions_since_best >= STALL_SESSIONS:
        status = "stalled"
    else:
        status = "holding"

    return ExerciseProgress(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        status=status,
        sessions_since_best=sessions_since_best,
        best_e1rm=best,
        latest_e1rm=e1rms[-1],
        last_session=last_session,
    )


@dataclass(frozen=True)
class StrengthTrend:
    """How an exercise's estimated max moved across a window of sessions."""

    best_e1rm: float
    change_kg: float
    points: tuple[float, ...]


def strength_trend(sessions: list[BenchmarkSet]) -> StrengthTrend:
    """Estimated max and the change across the given sessions, oldest first.

    The headline figure is the BEST estimated max in the window, not the latest: a set
    logged on a bad day does not undo a max that was really lifted. The change is
    measured from where the window started, which is what "stronger over four weeks"
    means to the person reading it.
    """
    ordered = sorted(sessions, key=lambda s: s.date)
    points = tuple(s.e1rm for s in ordered)
    if not points:
        return StrengthTrend(best_e1rm=0.0, change_kg=0.0, points=())
    best = max(points)
    return StrengthTrend(
        best_e1rm=best,
        change_kg=round(best - points[0], 1),
        points=points,
    )


def _region(muscle_group: str | None) -> str:
    """Movement pattern a muscle belongs to; unknown groups stand alone."""
    key = (muscle_group or "").strip().lower()
    return _MUSCLE_REGION.get(key, key or "unknown")


def classify_scope(stalled: list[ExerciseProgress]) -> str | None:
    """Systemic or local, the first question the course asks about a plateau (p.23)."""
    if not stalled:
        return None
    if len({_region(e.muscle_group) for e in stalled}) >= 2:
        return "systemic"
    if len(stalled) >= 2:
        return "local_muscle"
    return "local_exercise"


def intensified_rep_target(rep_target: int | None) -> int | None:
    """The lower rep target for a stalled exercise, or None when it cannot go lower.

    p.24: drop by at least 4 points, and never below 4 reps per set - under that the
    repetition volume is too low for maximum growth. When the target cannot be lowered,
    the course's next option is replacing the exercise.
    """
    if rep_target is None:
        return None
    lowered = rep_target - REP_TARGET_INTENSIFICATION
    return lowered if lowered >= MIN_REPS_PER_SET else None


def intensified_rep_range(reps_min: int | None, reps_max: int | None) -> tuple[int, int] | None:
    """The whole prescribed range after intensification, or None when it cannot go lower.

    The course lowers the rep *target* (p.24); a program prescribes a range, so the top
    of the range is what moves and the width is kept - a 10-15 range stays five reps
    wide at 6-11. The bottom is clamped at MIN_REPS_PER_SET, which can collapse a narrow
    range onto a single number (6-8 becomes 4-4); that is the intended end state, since
    below four reps per set the repetition volume is too low for growth.
    """
    lowered_max = intensified_rep_target(reps_max)
    if lowered_max is None:
        return None
    width = (reps_max - reps_min) if reps_min is not None and reps_max is not None else 0
    lowered_min = max(MIN_REPS_PER_SET, lowered_max - max(0, width))
    return lowered_min, lowered_max


def plateau_breaker_weight(
    weight_kg: float,
    reps: int,
    *,
    is_isolation: bool,
) -> float:
    """Weight for a plateau-breaker session: ~10% up, capped near a 3RM / 5RM (p.7).

    The cap is what keeps the breaker a low-volume, high-intensity session instead of a
    failed max attempt, so the load stays inside what the current strength supports.
    """
    cap_reps = BREAKER_CAP_REPS_ISOLATION if is_isolation else BREAKER_CAP_REPS_COMPOUND
    one_rm = calculate_1rm(weight_kg, reps).estimated_1rm
    # Weight that the estimated 1RM says can still be moved for cap_reps.
    cap_weight = one_rm / (1 + cap_reps / 30)
    return round(min(weight_kg * (1 + PLATEAU_BREAKER_PCT / 100), cap_weight), 2)


def decide_program_continuation(
    exercises: list[ExerciseProgress],
    *,
    total_weeks: int,
) -> ProgramDecision:
    """Extend, adjust, or stop.

    While nothing is stalling there is no reason to end a program on its planned date:
    the course calls scheduled cut-offs arbitrary (p.44) and rules out overtraining
    while strength is still going up (p.61). The cap is ours, not the course's.

    Safe to call at any point in the program - the adjustment actions apply whenever a
    stall appears, while `extend` only means "no reason to stop" and is acted on when the
    planned weeks run out.
    """
    stalled = [e for e in exercises if e.status == "stalled"]
    scope = classify_scope(stalled)

    if scope == "systemic":
        muscles = ", ".join(sorted({e.muscle_group or "?" for e in stalled}))
        return ProgramDecision(
            action="check_recovery",
            scope=scope,
            stalled=stalled,
            reason_bg=(
                f"Застой в несвързани мускулни групи ({muscles}). Причината най-вероятно е "
                "системна - възстановяване, сън, стрес или калории. Програмата не се променя, "
                "докато това не се провери."
            ),
        )

    if scope == "local_muscle":
        muscle = stalled[0].muscle_group
        names = ", ".join(e.exercise_name for e in stalled)
        return ProgramDecision(
            action="adjust_muscle",
            scope=scope,
            stalled=stalled,
            muscle_group=muscle,
            reason_bg=(
                f"Няколко упражнения за {muscle} са в застой ({names}). Първо се вдига честотата "
                "на групата, а ако графикът не позволява - броят серии."
            ),
        )

    if scope == "local_exercise":
        one = stalled[0]
        return ProgramDecision(
            action="adjust_exercise",
            scope=scope,
            stalled=stalled,
            exercise_name=one.exercise_name,
            muscle_group=one.muscle_group,
            reason_bg=(
                f"Само {one.exercise_name} е в застой. Сваля се целевият брой повторения "
                "(интензификация) или упражнението се сменя с алтернатива - останалата програма "
                "остава непроменена."
            ),
        )

    if total_weeks >= MAX_PROGRAM_WEEKS:
        return ProgramDecision(
            action="complete",
            scope=None,
            reason_bg=(
                f"Програмата стигна максималните {MAX_PROGRAM_WEEKS} седмици. Време е за нова, "
                "дори прогресът да продължава."
            ),
        )

    progressing = [e for e in exercises if e.status == "progressing"]
    return ProgramDecision(
        action="extend",
        scope=None,
        reason_bg=(
            f"Няма застой никъде ({len(progressing)} от {len(exercises)} упражнения с нов максимум). "
            "Умората още не е изпреварила възстановяването, така че програмата продължава."
        ),
    )
