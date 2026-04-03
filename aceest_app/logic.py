import hashlib
import random
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple


def estimate_calories(weight_kg: float, factor: float) -> int:
    """
    Simple calorie estimate used to show deterministic internal logic.
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if factor <= 0:
        raise ValueError("factor must be > 0")
    return int(round(weight_kg * factor))


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """
    BMI rounded to 1 decimal for stable API responses.
    """
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    if height_cm <= 0:
        raise ValueError("height_cm must be > 0")
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    return round(bmi, 1)


def bmi_category(bmi: float) -> Tuple[str, str]:
    if bmi < 18.5:
        return ("Underweight", "Potential nutrient deficiency; prioritize supervision.")
    if bmi < 25:
        return ("Normal", "Low risk if you maintain consistency and activity.")
    if bmi < 30:
        return ("Overweight", "Moderate risk; focus on adherence and progressive activity.")
    return ("Obese", "Higher risk; prioritize fat loss, consistency, and supervision.")


def parse_iso_date(value: str) -> date:
    """
    Parses `YYYY-MM-DD` ISO dates (no time component).
    """
    return datetime.strptime(value, "%Y-%m-%d").date()


def membership_status(membership_end: Optional[str], today: Optional[date] = None) -> str:
    if not membership_end:
        return "Unknown"
    today = today or date.today()
    end = parse_iso_date(membership_end)
    return "Active" if end >= today else "Expired"


PROGRAM_FACTORS: Dict[str, float] = {
    "fat loss": 24.0,
    "muscle gain": 35.0,
    "beginner": 26.0,
}


def program_factor(program: Optional[str]) -> float:
    if not program:
        return 25.0
    p = program.strip().lower()
    for key, factor in PROGRAM_FACTORS.items():
        if key in p:
            return factor
    return 25.0


EXERCISE_POOLS: Dict[str, List[str]] = {
    "full_body": ["Squat", "Deadlift", "Bench Press", "Overhead Press", "Row", "Pull-Up", "Lunge", "Plank"],
    "strength": ["Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row", "Lunge", "Hip Hinge"],
    "hypertrophy": [
        "Leg Press",
        "Incline Dumbbell Press",
        "Lat Pulldown",
        "Lateral Raise",
        "Bicep Curl",
        "Tricep Extension",
        "Leg Curl",
    ],
    "conditioning": ["Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings", "Jump Lunges"],
}


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _experience_plan_params(experience: str) -> Tuple[int, Tuple[int, int], Tuple[int, int], str]:
    exp = experience.strip().lower()
    if exp == "beginner":
        return (3, (2, 3), (8, 12), "full_body")
    if exp == "intermediate":
        return (4, (3, 4), (8, 15), "strength")
    if exp == "advanced":
        return (5, (4, 5), (6, 15), "hypertrophy")
    raise ValueError("experience must be beginner/intermediate/advanced")


def stable_seed(client_name: str, experience: str) -> int:
    payload = f"{client_name.strip().lower()}|{experience.strip().lower()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    # Take 8 hex chars => fits into 32-bit int.
    return int(digest[:8], 16)


def generate_program(
    experience: str,
    *,
    seed: Optional[int] = None,
    days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generates a deterministic program schedule when `seed` is provided.
    """
    default_days, sets_range, reps_range, focus = _experience_plan_params(experience)
    days = days or default_days

    rng = random.Random(seed)
    day_names = DAY_NAMES[:days]
    pool = EXERCISE_POOLS[focus]

    schedule: List[Dict[str, Any]] = []
    for day in day_names:
        items_count = 3 if days < 4 else 4
        exercises = rng.sample(pool, k=items_count if items_count <= len(pool) else len(pool))
        items = []
        for ex in exercises:
            sets = rng.randint(*sets_range)
            reps = rng.randint(*reps_range)
            items.append({"exercise": ex, "sets": sets, "reps": reps})
        schedule.append({"day": day, "items": items})

    return {"experience": experience.strip().lower(), "days": schedule}

