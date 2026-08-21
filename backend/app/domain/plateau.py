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

# A plateau is a session that repeats the previous one: the same weight for the same or
# fewer reps in the benchmark set. Progression Guidelines p.3-7 defines progress as more
# reps at the same weight (or the same reps at more weight), so the absence of both is
# the plateau - it needs no session count and no percentage.
#
# The course calls a *double* plateau at the same strength level cause to change the
# program (Periodization p.23). That is the second such session in a row: the first is
# answered inside the exercise with a plateau breaker.
DOUBLE_PLATEAU_SESSIONS = 2

# Reactive deload, p.46: the remaining sets are replaced with speed work at 60-70% of
# 1RM for 1-5 reps. Heavier than this stops being speed work and only deepens the hole.
SPEED_WORK_LOW_PCT = 60.0
SPEED_WORK_HIGH_PCT = 70.0
SPEED_WORK_MIN_REPS = 1
SPEED_WORK_MAX_REPS = 5

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
    # Sessions in a row that repeated the same weight without adding a rep. One is a
    # plateau, two or more is the double plateau that justifies changing the program.
    stalled_sessions: int = 0
    best_e1rm: float | None = None
    latest_e1rm: float | None = None
    last_session: SessionChange | None = None

    @property
    def double_plateau(self) -> bool:
        return self.stalled_sessions >= DOUBLE_PLATEAU_SESSIONS


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


def repeated_session(previous: BenchmarkSet, latest: BenchmarkSet) -> bool:
    """Did this session repeat the last one instead of beating it?

    The same weight for the same or fewer reps is the plateau: progress in this course is
    more reps at a given weight until the rep target is reached, then more weight
    (Progression Guidelines p.3). Adding weight and losing reps is *not* a plateau - that
    is the normal cost of a heavier first set, and the reps are worked back up from there.
    """
    return latest.weight_kg == previous.weight_kg and latest.reps <= previous.reps


def consecutive_stalls(sessions: list[BenchmarkSet]) -> int:
    """How many sessions in a row repeated the weight before them, counting back."""
    ordered = sorted(sessions, key=lambda s: s.date)
    stalls = 0
    for previous, latest in zip(reversed(ordered[:-1]), reversed(ordered[1:])):
        if not repeated_session(previous, latest):
            break
        stalls += 1
    return stalls


def classify_exercise(
    exercise_name: str,
    muscle_group: str | None,
    sessions: list[BenchmarkSet],
    training_status: int | None = None,
) -> ExerciseProgress:
    """Classify one exercise from its benchmark sets, oldest session first.

    `stalled` is decided by the sessions themselves, not by a count of sessions since a
    best: from the second session at a weight, the same load for the same or fewer reps
    means the exercise is stuck there. A lift that repeats its own best forever therefore
    reads as stalled, which is what it is - it was previously read as "progressing",
    because repeating a best kept resetting the counter.
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
    stalled_sessions = consecutive_stalls(ordered)

    if stalled_sessions:
        status = "stalled"
    elif sessions_since_best == 0:
        status = "progressing"
    else:
        status = "holding"

    return ExerciseProgress(
        exercise_name=exercise_name,
        muscle_group=muscle_group,
        status=status,
        sessions_since_best=sessions_since_best,
        stalled_sessions=stalled_sessions,
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


@dataclass(frozen=True)
class PlateauTechnique:
    """One course technique for getting an exercise moving again.

    `how_bg` carries the actual numbers, because "intensify" or "deload" without them is
    something the user still has to work out at the rack.
    """

    name: str          # plateau_breaker | reactive_deload | intensify | swap_exercise
    title_bg: str
    how_bg: str
    source_bg: str     # which part of the course this comes from


def reactive_deload_load(weight_kg: float, reps: int) -> tuple[float, float]:
    """Weight range for the speed work that replaces the remaining sets (p.46).

    60-70% of the estimated max: heavy enough to reach high activation, light enough that
    the bar still moves fast. The moment the speed drops it stops being a deload.
    """
    one_rm = calculate_1rm(weight_kg, reps).estimated_1rm
    return (
        round(one_rm * SPEED_WORK_LOW_PCT / 100, 1),
        round(one_rm * SPEED_WORK_HIGH_PCT / 100, 1),
    )


def reactive_deload(latest: BenchmarkSet, reps_lost: int) -> PlateauTechnique:
    """What to do with the rest of *this* session after the benchmark set fell short.

    p.46: fewer reps than last time is the signal. Just missing the last rep is answered
    with speed work; being well short means the remaining sets are dropped altogether,
    because speed work on top of that fatigue only digs the hole deeper.
    """
    if reps_lost >= 2:
        return PlateauTechnique(
            name="reactive_deload",
            title_bg="Реактивен deload: спри упражнението",
            how_bg=(
                f"Загуби {reps_lost} повторения спрямо миналия път. Пропусни останалите серии "
                "за това упражнение и продължи със следващото - при такава умора дори "
                "скоростната работа само задълбочава дупката."
            ),
            source_bg="Periodization & progress, стр. 46",
        )

    low, high = reactive_deload_load(latest.weight_kg, latest.reps)
    return PlateauTechnique(
        name="reactive_deload",
        title_bg="Реактивен deload: скоростна работа",
        how_bg=(
            f"Замени останалите серии с {SPEED_WORK_MIN_REPS}-{SPEED_WORK_MAX_REPS} бързи "
            f"повторения на серия с {low}-{high} кг. Ако скоростта падне забележимо, тежестта "
            "е висока - това вече не е deload."
        ),
        source_bg="Periodization & progress, стр. 46",
    )


def recommend_exercise_technique(
    progress: ExerciseProgress,
    *,
    latest: BenchmarkSet,
    reps_min: int | None,
    reps_max: int | None,
    is_isolation: bool,
) -> PlateauTechnique:
    """The course's answer for one stalled exercise, at the stage it has reached.

    First plateau: a breaker session (p.7) - the exercise is not the problem yet, one
    heavy low-volume session usually is enough. Double plateau at the same strength
    level: the program for that exercise changes (p.23-24), by lowering the rep target if
    there is room, and by replacing the exercise if there is not.
    """
    if not progress.double_plateau:
        breaker = plateau_breaker_weight(latest.weight_kg, latest.reps, is_isolation=is_isolation)
        cap = BREAKER_CAP_REPS_ISOLATION if is_isolation else BREAKER_CAP_REPS_COMPOUND
        return PlateauTechnique(
            name="plateau_breaker",
            title_bg="Пробивна сесия",
            how_bg=(
                f"Следващия път качи на {breaker} кг за {cap}-{cap + 2} повторения - една тежка "
                "серия с малък обем. След нея се връщаш на предишната тежест и качваш "
                "повторенията оттам."
            ),
            source_bg="Progression Guidelines, стр. 7",
        )

    intensified = intensified_rep_range(reps_min, reps_max)
    if intensified:
        low, high = intensified
        # A narrow range collapses onto a single number at the growth floor; "4-4 reps"
        # is technically what it says and reads like a bug.
        target = f"{low}" if low == high else f"{low}-{high}"
        return PlateauTechnique(
            name="intensify",
            title_bg="Интензификация: по-малко повторения",
            how_bg=(
                f"Свали целта от {reps_min}-{reps_max} на {target} повторения и качи тежестта. "
                "По-високата интензивност вдига силата и връща прогресията."
            ),
            source_bg="Periodization & progress, стр. 24",
        )

    return PlateauTechnique(
        name="swap_exercise",
        title_bg="Смени упражнението",
        how_bg=(
            f"Повторенията вече не могат да слязат под {MIN_REPS_PER_SET} на серия, без обемът "
            "да падне под нужния за растеж. Замени упражнението с друго за същото движение - "
            "често застоят е от прекалено голяма стъпка на тежестта, а не от самия мускул. "
            "Ако държиш да останеш на това упражнение, следващата стъпка по курса е "
            "периодизация."
        ),
        source_bg="Periodization & progress, стр. 24",
    )


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

    A *first* plateau never changes the program: the course answers it inside the
    exercise with a breaker session (p.7), and only a double plateau at the same strength
    level is cause to change the plan (p.23). So the program-level decision is made on
    the double plateaus, and the single ones come back as `break_plateau`.
    """
    stalled = [e for e in exercises if e.status == "stalled"]
    changing = [e for e in stalled if e.double_plateau]
    scope = classify_scope(changing)

    if scope == "systemic":
        muscles = ", ".join(sorted({e.muscle_group or "?" for e in changing}))
        return ProgramDecision(
            action="check_recovery",
            scope=scope,
            stalled=changing,
            reason_bg=(
                f"Застой в несвързани мускулни групи ({muscles}). Причината най-вероятно е "
                "системна - възстановяване, сън, стрес или калории. Програмата не се променя, "
                "докато това не се провери."
            ),
        )

    if scope == "local_muscle":
        muscle = changing[0].muscle_group
        names = ", ".join(e.exercise_name for e in changing)
        return ProgramDecision(
            action="adjust_muscle",
            scope=scope,
            stalled=changing,
            muscle_group=muscle,
            reason_bg=(
                f"Няколко упражнения за {muscle} са в двоен застой ({names}). Първо се вдига "
                "честотата на групата, а ако графикът не позволява - броят серии."
            ),
        )

    if scope == "local_exercise":
        one = changing[0]
        return ProgramDecision(
            action="adjust_exercise",
            scope=scope,
            stalled=changing,
            exercise_name=one.exercise_name,
            muscle_group=one.muscle_group,
            reason_bg=(
                f"{one.exercise_name} е в застой {one.stalled_sessions} поредни сесии на същата "
                "тежест. Пробивната сесия не сработи, така че се сваля целевият брой повторения "
                "или упражнението се сменя - останалата програма остава непроменена."
            ),
        )

    if stalled:
        names = ", ".join(e.exercise_name for e in stalled)
        return ProgramDecision(
            action="break_plateau",
            scope="local_exercise",
            stalled=stalled,
            exercise_name=stalled[0].exercise_name,
            muscle_group=stalled[0].muscle_group,
            reason_bg=(
                f"Застой на същата тежест: {names}. Програмата не се променя заради една такава "
                "сесия - отговорът е пробивна сесия в самото упражнение."
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
