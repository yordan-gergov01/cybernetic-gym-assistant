"""
calculators.py - Calculator Implementations
Used by the AI agent when building individual user programs.

BF% Assessment: Visual method via Gemini Vision
  - User uploads photos (front, back, side)
  - Gemini compares with "Body fat percentage visual reference guide PTC.pdf"
  - BMI estimate used only as fallback when no photos provided

Calculators:
  1. estimate_bf_bmi() - fallback BF% from BMI (no photos)
  2. calculate_energy_intake() - BMR (Katch-McArdle) → TDEE → macros
  3. calculate_energy_balance() - verify expected body comp change
  4. calculate_1rm() - Epley 1RM from working set
  5. calculate_optimal_volume() - optimal sets/week per muscle group
  6. run_all_calculators() - convenience wrapper for program generation
"""

from dataclasses import dataclass
from typing import Literal


# BF% - BMI-BASED FALLBACK
#    Primary method: Gemini Vision vs visual reference guide PDF
#    This is used ONLY when the user does not upload photos

@dataclass
class BFResult:
    bf_percentage: float
    lbm_kg: float
    fm_kg: float
    method: str


def estimate_bf_bmi(
    age: int,
    sex: Literal['male', 'female'],
    height_cm: float,
    bodyweight_kg: float,
) -> BFResult:
    """
    BMI-based BF% estimate (Deurenberg formula).
    Fallback only - visual assessment via Gemini Vision is preferred.
    Formula from Energy intake calculator.xlsx.
    """
    bmi = bodyweight_kg / (height_cm / 100) ** 2
    pct = 1.2 * bmi + 0.23 * age - 10.8 * (1 if sex == 'male' else 0) - 5.4
    fm = round(bodyweight_kg * pct / 100, 1)
    lbm = round(bodyweight_kg - fm, 1)
    return BFResult(round(pct, 1), lbm, fm, 'BMI-based estimate (fallback - no photos)')



# ENERGY INTAKE — BMR / TDEE / MACROS

@dataclass
class EnergyIntakeResult:
    lbm_kg: float
    bmr_kcal: float
    tdee_kcal: float
    target_kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    goal: str


def calculate_energy_intake(
    bodyweight_kg: float,
    body_fat_pct: float,
    activity_level: Literal['sedentary', 'light', 'moderate', 'active', 'very_active'],
    goal: Literal['bulk', 'cut', 'maintain', 'aggressive_cut'],
    training_days_per_week: int = 4,
    sex: Literal['male', 'female'] = 'male',
) -> EnergyIntakeResult:
    """
    BMR via Katch-McArdle (LBM-based - more accurate than Harris-Benedict).
    Activity multipliers and macro targets from Henselmans Energy intake calculator.xlsx.
    """
    lbm_kg = bodyweight_kg * (1 - body_fat_pct / 100)
    bmr = 370 + (21.6 * lbm_kg)

    pa_map = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9,
    }
    tdee = bmr * pa_map[activity_level] + (training_days_per_week * 100 / 7)

    adj = {'bulk': +250, 'maintain': 0, 'cut': -500, 'aggressive_cut': -750}
    target = tdee + adj[goal]

    p_mult = 2.0 if goal in ('cut', 'aggressive_cut') else 1.8
    prot_g = round(bodyweight_kg * p_mult)
    fat_g = round(max(bodyweight_kg * 0.8, target * 0.20 / 9))
    carb_g = round(max(0, (target - prot_g * 4 - fat_g * 9) / 4))

    return EnergyIntakeResult(
        lbm_kg=round(lbm_kg, 1), bmr_kcal=round(bmr), tdee_kcal=round(tdee),
        target_kcal=round(target), protein_g=prot_g, fat_g=fat_g, carbs_g=carb_g, goal=goal,
    )


# ENERGY BALANCE - VERIFY EXPECTED BODY COMP CHANGE

@dataclass
class EnergyBalanceResult:
    daily_balance_kcal: float
    weekly_balance_kcal: float
    expected_bw_change_kg_week: float


def calculate_energy_balance(
    lbm_change_kg: float,
    fm_change_kg: float,
) -> EnergyBalanceResult:
    """
    Energy density constants from the Energy Balance Calculator:
      LBM : 1,817 kcal/kg
      Fat : 9,081 kcal/kg
    """
    weekly = lbm_change_kg * 1817 + fm_change_kg * 9081
    return EnergyBalanceResult(
        daily_balance_kcal=round(weekly / 7, 1),
        weekly_balance_kcal=round(weekly, 1),
        expected_bw_change_kg_week=round(lbm_change_kg + fm_change_kg, 3),
    )


# ONE REP MAX

@dataclass
class OneRMResult:
    estimated_1rm: float
    weight_at_reps: dict   # {reps: weight} for common rep ranges
    formula: str


def calculate_1rm(
    weight: float,
    reps: int,
    formula: Literal['epley', 'brzycki', 'lombardi'] = 'epley',
) -> OneRMResult:
    """
    Estimate 1RM from a working set.
    Epley is the default - same as used in the 1RM calculator.
    """
    if reps == 1:
        orm = weight
    elif formula == 'epley':
        orm = weight * (1 + reps / 30)
    elif formula == 'brzycki':
        orm = weight / (1.0278 - 0.0278 * reps)
    else:
        orm = weight * (reps ** 0.10)

    targets = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]
    w_at_reps = {r: round(orm if r == 1 else orm / (1 + r / 30), 1) for r in targets}

    return OneRMResult(round(orm, 1), w_at_reps, formula)


def calculate_bodyweight_1rm(
    bodyweight: float,
    external_weight: float,
    reps: int,
) -> OneRMResult:
    """1RM for bodyweight exercises (pull-ups, dips). Total load = BW + external."""
    r = calculate_1rm(bodyweight + external_weight, reps)
    r.estimated_1rm = round(r.estimated_1rm - bodyweight, 1)
    r.formula = f'bodyweight_epley (BW={bodyweight}kg)'
    return r


# TRAINING VOLUME

@dataclass
class VolumeResult:
    muscle_groups: dict   # {muscle: recommended_sets_per_week}
    training_status: int
    is_female: bool
    notes: str


def calculate_optimal_volume(
    training_status: Literal[1, 2, 3],   # 1=novice, 2=intermediate, 3=advanced
    is_female: bool = False,
    priority_muscles: list | None = None,
) -> VolumeResult:
    """
    Optimal weekly sets per muscle group by training status.
    Female lower body +20% per Fitness for Women module.
    Priority muscles receive +4 sets above baseline.
    """
    BASE = {
        'chest': [10, 12, 16],
        'back': [10, 14, 18],
        'shoulders': [ 8, 12, 16],
        'biceps': [ 6, 10, 14],
        'triceps': [ 6, 10, 14],
        'quads': [10, 14, 18],
        'hamstrings': [ 8, 10, 14],
        'glutes': [ 8, 12, 16],
        'calves': [ 6, 10, 14],
        'abs': [ 4,  8, 12],
        'rear_delts': [ 6, 10, 14],
    }
    idx = training_status - 1
    muscles = {}
    for m, v in BASE.items():
        sets = v[idx]
        if is_female and m in ('glutes', 'hamstrings', 'quads'):
            sets = round(sets * 1.2)
        if priority_muscles and m in priority_muscles:
            sets += 4
        muscles[m] = sets

    label = {1: 'Novice', 2: 'Intermediate', 3: 'Advanced'}[training_status]
    notes = (
        f"Based on {label} status. "
        f"{'Female lower body +20% applied. ' if is_female else ''}"
        f"{'Priority: ' + ', '.join(priority_muscles) + '. ' if priority_muscles else ''}"
        "MEV -> MAV progression recommended."
    )
    return VolumeResult(muscles, training_status, is_female, notes)


# GOAL VALIDATION
#    Called BEFORE energy intake to determine the correct goal

@dataclass
class GoalValidationResult:
    recommended_goal: str
    override: bool          # True if agent overrides user's stated goal
    override_reason: str
    bf_status: str          # 'too_high' | 'optimal' | 'too_low'


def validate_goal(
    bf_percentage: float,
    sex: Literal['male', 'female'],
    user_stated_goal: Literal['bulk', 'cut', 'maintain', 'aggressive_cut'],
) -> GoalValidationResult:
    """
    Validate user's stated goal against their BF%.

    Men: cut recommended if BF > 15%, bulk if BF < 10%
    Women: cut recommended if BF > 25%, bulk if BF < 18%
    """
    thresholds = {
        'male': {'cut_above': 15.0, 'bulk_below': 10.0},
        'female': {'cut_above': 25.0, 'bulk_below': 18.0},
    }
    t = thresholds[sex]

    if bf_percentage > t['cut_above']:
        bf_status = 'too_high'
        recommended = 'cut'
        override = user_stated_goal not in ('cut', 'aggressive_cut')
        reason = (
            f"BF% ({bf_percentage}%) is above the optimal range for {sex}s "
            f"(>{t['cut_above']}%). Cutting first improves insulin sensitivity, "
            "nutrient partitioning, and long-term muscle gain potential."
            if override else ''
        )
    elif bf_percentage < t['bulk_below']:
        bf_status = 'too_low'
        recommended = 'bulk'
        override = user_stated_goal in ('cut', 'aggressive_cut')
        reason = (
            f"BF% ({bf_percentage}%) is below the healthy floor for {sex}s "
            f"(<{t['bulk_below']}%). Cutting further risks hormonal disruption "
            "and excessive muscle loss."
            if override else ''
        )
    else:
        bf_status = 'optimal'
        recommended = user_stated_goal
        override = False
        reason = ''

    return GoalValidationResult(recommended, override, reason, bf_status)

# CONVENIENCE - Run all calculators from user profile dict
#    Called by the AI agent during program generation

def run_all_calculators(user_profile: dict) -> dict:
    """
    Full calculator pipeline from a user profile dict.

    Expected keys:
      bodyweight_kg, body_fat_pct, height_cm, age, sex,
      activity_level, goal (stated), training_status (1-3),
      training_days_per_week, priority_muscles (optional),
      lifts: {lift_name: {weight, reps}}
    """
    results = {}

    # Step 1: Validate goal against BF%
    results['goal_validation'] = validate_goal(
        bf_percentage = user_profile['body_fat_pct'],
        sex = user_profile.get('sex', 'male'),
        user_stated_goal = user_profile['goal'],
    )
    actual_goal = results['goal_validation'].recommended_goal

    # Step 2: Energy intake with validated goal
    results['energy'] = calculate_energy_intake(
        bodyweight_kg = user_profile['bodyweight_kg'],
        body_fat_pct = user_profile['body_fat_pct'],
        activity_level = user_profile['activity_level'],
        goal = actual_goal,
        training_days_per_week = user_profile.get('training_days_per_week', 4),
        sex = user_profile.get('sex', 'male'),
    )

    # Step 3: Training volume
    results['volume'] = calculate_optimal_volume(
        training_status = user_profile['training_status'],
        is_female = user_profile.get('sex') == 'female',
        priority_muscles = user_profile.get('priority_muscles'),
    )

    # Step 4: 1RM for all lifts
    results['lifts'] = {
        lift: calculate_1rm(data['weight'], data['reps'])
        for lift, data in user_profile.get('lifts', {}).items()
    }

    return results
