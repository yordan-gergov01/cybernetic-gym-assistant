
"""
calculators.py - Calculator Implementations
Used by the AI agent when building individual user programs.
"""
from dataclasses import dataclass
from typing import Literal


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
    activity_level: Literal['sedentary','light','moderate','active','very_active'],
    goal: Literal['bulk','cut','maintain','aggressive_cut'],
    training_days_per_week: int = 4,
    sex: Literal['male','female'] = 'male',
) -> EnergyIntakeResult:
    """BMR via Katch-McArdle. Activity multipliers from Henselmans Energy intake calculator."""
    lbm_kg = bodyweight_kg * (1 - body_fat_pct / 100)
    bmr = 370 + (21.6 * lbm_kg) # Katch-McArdle
    pa_map = {'sedentary':1.2,'light':1.375,'moderate':1.55,'active':1.725,'very_active':1.9}
    pa = pa_map[activity_level]
    tdee = bmr * pa + (training_days_per_week * 100 / 7)
    adj = {'bulk':+250,'maintain':0,'cut':-500,'aggressive_cut':-750}
    target = tdee + adj[goal]
    p_mult = 2.0 if goal in ('cut','aggressive_cut') else 1.8
    prot_g = round(bodyweight_kg * p_mult)
    fat_g  = round(max(bodyweight_kg * 0.8, target * 0.20 / 9))
    carb_g = round(max(0, (target - prot_g*4 - fat_g*9) / 4))
    return EnergyIntakeResult(round(lbm_kg,1), round(bmr), round(tdee),
                               round(target), prot_g, fat_g, carb_g, goal)


@dataclass
class EnergyBalanceResult:
    daily_balance_kcal: float
    weekly_balance_kcal: float
    expected_bw_change_kg_week: float

def calculate_energy_balance(lbm_change_kg: float, fm_change_kg: float) -> EnergyBalanceResult:
    """Energy density: LBM=1817 kcal/kg, Fat=9081 kcal/kg (from spreadsheet)."""
    weekly = lbm_change_kg * 1817 + fm_change_kg * 9081
    return EnergyBalanceResult(round(weekly/7,1), round(weekly,1),
                                round(lbm_change_kg+fm_change_kg,3))


@dataclass
class CaliperBFResult:
    bf_percentage: float
    lbm_kg: float
    fm_kg: float
    method: str

def _bf_from_density(density, bw): 
    pct = ((4.95/density)-4.50)*100
    return pct, round(bw*(1-pct/100),1), round(bw*pct/100,1)

def calculate_bf_3site_men(age,chest_mm,abdomen_mm,thigh_mm,bodyweight_kg) -> CaliperBFResult:
    S = chest_mm+abdomen_mm+thigh_mm
    d = 1.10938-(0.0008267*S)+(0.0000016*S**2)-(0.0002574*age)
    pct,lbm,fm = _bf_from_density(d, bodyweight_kg)
    return CaliperBFResult(round(pct,1), lbm, fm, 'Jackson-Pollock 3-site (men)')

def calculate_bf_3site_women(age,tricep_mm,suprailiac_mm,thigh_mm,bodyweight_kg) -> CaliperBFResult:
    S = tricep_mm+suprailiac_mm+thigh_mm
    d = 1.099492-(0.0009929*S)+(0.0000023*S**2)-(0.0001392*age)
    pct,lbm,fm = _bf_from_density(d, bodyweight_kg)
    return CaliperBFResult(round(pct,1), lbm, fm, 'Jackson-Pollock 3-site (women)')

def estimate_bf_no_caliper(age,sex,height_cm,bodyweight_kg) -> CaliperBFResult:
    """BMI-based estimate. Formula from Henselmans PTC (Energy intake calculator)."""
    bmi = bodyweight_kg / (height_cm/100)**2
    pct = 1.2*bmi + 0.23*age - 10.8*(1 if sex=='male' else 0) - 5.4
    fm = round(bodyweight_kg*pct/100, 1)
    lbm = round(bodyweight_kg - fm, 1)
    return CaliperBFResult(round(pct,1), lbm, fm, 'BMI-based estimate (no calipers)')


@dataclass
class OneRMResult:
    estimated_1rm: float
    weight_at_reps: dict
    formula: str

def calculate_1rm(weight:float, reps:int,
                  formula:Literal['epley','brzycki','lombardi']='epley') -> OneRMResult:
    if reps == 1:
        orm = weight
    elif formula == 'epley':
        orm = weight * (1 + reps/30)
    elif formula == 'brzycki':
        orm = weight / (1.0278 - 0.0278*reps)
    else:
        orm = weight * (reps**0.10)
    targets = [1,2,3,4,5,6,8,10,12,15,20]
    w_at_r = {r: round(orm if r==1 else orm/(1+r/30), 1) for r in targets}
    return OneRMResult(round(orm,1), w_at_r, formula)

def calculate_bodyweight_1rm(bodyweight, external_weight, reps) -> OneRMResult:
    r = calculate_1rm(bodyweight+external_weight, reps)
    r.estimated_1rm = round(r.estimated_1rm - bodyweight, 1)
    r.formula = f'bodyweight_epley (BW={bodyweight}kg)'
    return r


@dataclass
class VolumeResult:
    muscle_groups: dict
    training_status: int
    is_female: bool
    notes: str

def calculate_optimal_volume(
    training_status: Literal[1,2,3],
    is_female: bool = False,
    priority_muscles: list = None,
) -> VolumeResult:
    BASE = {
        'chest':[10,12,16], 'back':[10,14,18],
        'shoulders':[8, 12,16], 'biceps':[6, 10,14],
        'triceps':[6, 10,14], 'quads':[10,14,18],
        'hamstrings':[8, 10,14], 'glutes':[8, 12,16],
        'calves':[6, 10,14], 'abs':[4, 8,12],
        'rear_delts':[6, 10,14],
    }
    idx = training_status - 1
    muscles = {}
    for m, v in BASE.items():
        sets = v[idx]
        if is_female and m in ('glutes','hamstrings','quads'): sets = round(sets*1.2)
        if priority_muscles and m in priority_muscles: sets += 4
        muscles[m] = sets
    label = {1:'Novice',2:'Intermediate',3:'Advanced'}[training_status]
    notes = (f"Based on {label} status. "
             f"{'Female lower body +20% applied. ' if is_female else ''}"
             f"{'Priority: '+', '.join(priority_muscles)+'.' if priority_muscles else ''}"
             " MEV -> MAV progression recommended.")
    return VolumeResult(muscles, training_status, is_female, notes)



def run_all_calculators(user_profile: dict) -> dict:
    results = {}
    results['energy'] = calculate_energy_intake(
        bodyweight_kg = user_profile['bodyweight_kg'],
        body_fat_pct = user_profile['body_fat_pct'],
        activity_level = user_profile['activity_level'],
        goal = user_profile['goal'],
        training_days_per_week = user_profile.get('training_days_per_week', 4),
        sex = user_profile.get('sex', 'male'),
    )
    results['volume'] = calculate_optimal_volume(
        training_status = user_profile['training_status'],
        is_female = user_profile.get('sex') == 'female',
        priority_muscles = user_profile.get('priority_muscles'),
    )
    results['lifts'] = {
        lift: calculate_1rm(data['weight'], data['reps'])
        for lift, data in user_profile.get('lifts', {}).items()
    }
    return results
