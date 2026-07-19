import json
import logging
from datetime import date as date_type

import httpx
from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db
from deps import get_current_user
from models import FoodLog, NutritionTarget, User
from prompts.registry import get_prompt
from schemas import DailyNutritionSummary, FoodLogCreate

router = APIRouter(prefix="/food", tags=["food"])
logger = logging.getLogger(__name__)

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class FoodItem(BaseModel):
    food_name_en: str
    food_name_bg: str
    quantity_g: float
    cooking_method: str = ""


async def extract_food_items(text: str) -> list[FoodItem]:
    prompt = get_prompt("food_extraction")(text)
    r = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=400,
    )
    data = json.loads(r.choices[0].message.content)
    return [FoodItem(**i) for i in data.get("items", [])]


def parse_usda_nutrients(food_data: dict, qty: float) -> dict:
    calorie_ids = {1008, 1062, 2047, 2048}
    nmap = {1003: "protein_g", 1004: "fat_g", 1005: "carbs_g", 2000: "sugar_g", 1079: "fiber_g"}
    nutrients = {}
    for n in food_data.get("foodNutrients", []):
        nid = n.get("nutrientId") or n.get("nutrient", {}).get("id")
        val = n.get("value") or n.get("amount") or 0
        if nid in calorie_ids and "calories" not in nutrients and val > 0:
            nutrients["calories"] = val
        elif nid in nmap and nmap[nid] not in nutrients:
            nutrients[nmap[nid]] = val
    if not nutrients.get("calories"):
        p, f, c = nutrients.get("protein_g", 0), nutrients.get("fat_g", 0), nutrients.get("carbs_g", 0)
        nutrients["calories"] = round(p * 4 + f * 9 + c * 4, 1)
    scale = qty / 100.0
    return {k: round(v * scale, 1) for k, v in nutrients.items()}


async def lookup_usda(item: FoodItem) -> dict | None:
    try:
        q = item.food_name_en + (f" {item.cooking_method}" if item.cooking_method else "")
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings.USDA_BASE_URL.rstrip('/')}/foods/search",
                params={
                    "api_key": settings.USDA_API_KEY,
                    "query": q,
                    "dataType": ["Foundation", "SR Legacy"],
                    "pageSize": 3,
                },
                timeout=8,
            )
            foods = r.json().get("foods", [])
        if not foods:
            return None
        ntr = parse_usda_nutrients(foods[0], item.quantity_g)
        return {"food_name": item.food_name_bg, "source": "USDA", "confidence": "high", "quantity_g": item.quantity_g, **ntr}
    except Exception:
        logger.info("USDA lookup failed for '%s'; falling back to LLM estimate", item.food_name_en, exc_info=True)
        return None


async def lookup_llm(item: FoodItem) -> dict:
    prompt = get_prompt("food_llm_estimate")(
        food_name_en=item.food_name_en,
        cooking_method=item.cooking_method,
        quantity_g=item.quantity_g,
        food_name_bg=item.food_name_bg,
    )
    r = await openai_client.chat.completions.create(
        model=settings.PRIMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=100,
    )
    d = json.loads(r.choices[0].message.content)
    return {
        "food_name": item.food_name_bg,
        "source": "LLM estimate",
        "confidence": "low",
        "quantity_g": item.quantity_g,
        **{k: float(v) for k, v in d.items()},
    }


@router.post("", status_code=201)
async def log_food(data: FoodLogCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    items = await extract_food_items(data.food_description)
    logged = []
    for item in items:
        nutrition = await lookup_usda(item) or await lookup_llm(item)
        entry = FoodLog(
            user_id=user.id,
            date=data.date,
            meal_type=data.meal_type,
            food_name=nutrition["food_name"],
            quantity_g=nutrition.get("quantity_g"),
            calories=nutrition.get("calories"),
            protein_g=nutrition.get("protein_g"),
            fat_g=nutrition.get("fat_g"),
            carbs_g=nutrition.get("carbs_g"),
            sugar_g=nutrition.get("sugar_g"),
            fiber_g=nutrition.get("fiber_g"),
            source=nutrition.get("source"),
            confidence=nutrition.get("confidence"),
        )
        db.add(entry)
        logged.append(entry)
    await db.commit()
    return {
        "logged": len(logged),
        "entries": [{"food_name": e.food_name, "calories": e.calories, "protein_g": e.protein_g} for e in logged],
    }


@router.get("/daily/{log_date}", response_model=DailyNutritionSummary)
async def get_daily(log_date: date_type, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    entries_r = await db.execute(select(FoodLog).where(FoodLog.user_id == user.id, FoodLog.date == log_date))
    entries = entries_r.scalars().all()
    totals = {k: round(sum(getattr(e, k) or 0 for e in entries), 1) for k in ["calories", "protein_g", "fat_g", "carbs_g"]}
    nt_r = await db.execute(select(NutritionTarget).where(NutritionTarget.user_id == user.id))
    nt = nt_r.scalar_one_or_none()
    targets = (
        {
            "calories": nt.calories or 2000,
            "protein_g": nt.protein_g or 150,
            "fat_g": nt.fat_g or 60,
            "carbs_g": nt.carbs_g or 200,
        }
        if nt
        else {}
    )
    remaining = {k: round(targets.get(k, 0) - totals.get(k, 0), 1) for k in totals}
    pct = {k: round(totals.get(k, 0) / targets.get(k, 1) * 100, 1) if targets.get(k) else 0 for k in totals}
    return DailyNutritionSummary(
        date=log_date, entries=entries, totals=totals, targets=targets, remaining=remaining, pct_complete=pct
    )


@router.delete("/{entry_id}", status_code=204)
async def delete_food_entry(entry_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(FoodLog).where(FoodLog.id == entry_id, FoodLog.user_id == user.id))
    entry = r.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Entry not found")
    await db.delete(entry)
    await db.commit()
