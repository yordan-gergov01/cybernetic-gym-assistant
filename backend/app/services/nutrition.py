"""What the user has eaten today against what they were told to eat.

The numbers come from the logged entries and the stored targets - never from a model.
It lives here rather than in the food route because the coach needs the same answer when
someone asks how many calories they have left, and two copies of this arithmetic would
eventually disagree with each other.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodLog, NutritionTarget

MACROS = ("calories", "protein_g", "fat_g", "carbs_g")

# What the app assumes when a profile has no stored target yet. Same values the food
# screen has always shown, kept in one place now that two callers read them.
_FALLBACK_TARGETS = {"calories": 2000, "protein_g": 150, "fat_g": 60, "carbs_g": 200}


@dataclass
class DailyIntake:
    """Eaten, prescribed, and what is left of the day.

    `targets` is empty when the user has no nutrition target at all, which is different
    from a target of zero: nothing has been prescribed, so nothing is left to eat by.
    """

    entries: list[FoodLog]
    totals: dict[str, float]
    targets: dict[str, float]
    remaining: dict[str, float]
    pct_complete: dict[str, float]

    @property
    def has_targets(self) -> bool:
        return bool(self.targets)


async def daily_intake(db: AsyncSession, user_id: str, day: date_type) -> DailyIntake:
    r = await db.execute(select(FoodLog).where(FoodLog.user_id == user_id, FoodLog.date == day))
    entries = list(r.scalars().all())
    totals = {macro: round(sum(getattr(e, macro) or 0 for e in entries), 1) for macro in MACROS}

    nt = (
        await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == user_id))
    ).scalar_one_or_none()
    targets = (
        {macro: getattr(nt, macro) or _FALLBACK_TARGETS[macro] for macro in MACROS} if nt else {}
    )

    remaining = {macro: round(targets.get(macro, 0) - totals[macro], 1) for macro in MACROS}
    pct = {
        macro: round(totals[macro] / targets[macro] * 100, 1) if targets.get(macro) else 0
        for macro in MACROS
    }
    return DailyIntake(
        entries=entries, totals=totals, targets=targets, remaining=remaining, pct_complete=pct
    )
