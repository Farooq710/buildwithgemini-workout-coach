"""Safety, medical red-flag interception, and contraindication validation engine."""

import re
from typing import List, Tuple, Optional
from workout_coach.core.models import WorkoutPlan, FitnessProfile
from workout_coach.core.exercise_library import get_exercise_by_id

# Acute red-flag patterns that necessitate immediate exercise termination
RED_FLAG_PATTERNS = [
    r"\bchest\s+pain\b",
    r"\bsharp\s+pain\b",
    r"\bpopping\s+sound\b",
    r"\bpop\s+in\s+my\b",
    r"\bfeeling\s+(?:dizzy|lightheaded|faint)\b",
    r"\bdizziness\b",
    r"\blightheadedness\b",
    r"\bpassed\s+out\b",
    r"\bheart\s+palpitations?\b",
    r"\bracing\s+heart\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bcan'?t\s+breathe\b",
    r"\bradiating\s+pain\b",
    r"\bnumbness\b",
    r"\btingling\s+(?:down|in)\s+my\b",
]

COMPILED_RED_FLAGS = [re.compile(p, re.IGNORECASE) for p in RED_FLAG_PATTERNS]


def scan_for_red_flags(text: str) -> Optional[str]:
    """Inspect text for symptoms requiring medical intervention.
    
    Returns an urgent warning string if any red flag matches, otherwise None.
    """
    if not text:
        return None

    for pattern in COMPILED_RED_FLAGS:
        if pattern.search(text):
            return (
                "🚨 SAFETY ALERT: You reported symptoms (such as sharp pain, chest tightness, or dizziness) "
                "that may indicate acute strain or a medical issue. Please STOP exercising immediately, "
                "rest in a safe position, and seek evaluation from a healthcare professional or emergency care. "
                "Do not attempt to push through sharp or cardiovascular symptoms."
            )
    return None


def validate_plan_safety(plan: WorkoutPlan, profile: FitnessProfile) -> Tuple[bool, List[str]]:
    """Verify that a generated workout plan complies with declared limitations and equipment availability."""
    violations: List[str] = []
    
    user_limitations = set([lim.lower().strip() for lim in profile.limitations])
    user_equipment = set([eq.lower().strip() for eq in profile.available_equipment])
    user_equipment.add("bodyweight")

    total_plan_sets = 0
    for session in plan.sessions:
        session_sets = 0
        for p_ex in session.exercises:
            session_sets += p_ex.target_sets
            total_plan_sets += p_ex.target_sets

            ex_def = get_exercise_by_id(p_ex.exercise_id)
            if not ex_def:
                violations.append(f"Exercise ID '{p_ex.exercise_id}' not found in official catalog.")
                continue

            # 1. Check Contraindications
            if user_limitations:
                ex_contra = set([c.lower().strip() for c in ex_def.contraindications])
                clashes = user_limitations.intersection(ex_contra)
                if clashes:
                    violations.append(
                        f"Exercise '{ex_def.name}' is contraindicated for user limitation(s): {', '.join(clashes)}."
                    )

            # 2. Check Equipment Compatibility
            ex_eq = set([eq.lower().strip() for eq in ex_def.equipment_required])
            missing_eq = ex_eq - user_equipment
            if missing_eq:
                violations.append(
                    f"Exercise '{ex_def.name}' requires {missing_eq} which is not in user's available equipment."
                )

            # 3. Check parameter sanity
            if p_ex.target_sets > 8:
                violations.append(f"Excessive volume: '{ex_def.name}' prescribes {p_ex.target_sets} sets.")

        if session_sets > 30:
            violations.append(f"Session '{session.day_name}' has excessive volume ({session_sets} total sets).")

    is_safe = len(violations) == 0
    return is_safe, violations
