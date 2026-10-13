"""Curated, grounded exercise library with biomechanical tags, cues, and contraindications."""

from typing import List, Optional, Dict
from workout_coach.core.models import Exercise, ExerciseCategory, MovementPattern


EXERCISE_CATALOG: List[Exercise] = [
    # --- CHEST / PUSH ---
    Exercise(
        id="ex_barbell_bench_press",
        name="Barbell Bench Press",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["chest", "triceps"],
        secondary_muscles=["anterior_deltoids"],
        equipment_required=["barbell", "bench"],
        instructions="Lie flat on bench, grip bar slightly wider than shoulder width. Retract scapulae, unrack, lower under control to mid-chest, then press upwards to full lockout.",
        substitutions=["ex_dumbbell_bench_press", "ex_pushups"],
        contraindications=["shoulder_impingement", "wrist_pain"]
    ),
    Exercise(
        id="ex_dumbbell_bench_press",
        name="Dumbbell Bench Press",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["chest", "triceps"],
        secondary_muscles=["anterior_deltoids"],
        equipment_required=["dumbbells", "bench"],
        instructions="Lie on flat bench holding dumbbells at chest height with neutral or 45-degree angled grip. Press upward smoothly while keeping shoulders packed.",
        substitutions=["ex_pushups", "ex_floor_press"],
        contraindications=[]
    ),
    Exercise(
        id="ex_pushups",
        name="Push-ups",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["chest", "triceps", "core"],
        secondary_muscles=["anterior_deltoids"],
        equipment_required=["bodyweight"],
        instructions="Maintain rigid plank posture from heels to head. Lower chest until 1-2 inches off floor with elbows at 45-degree angle, then press through palms to start.",
        substitutions=["ex_incline_pushups", "ex_dumbbell_bench_press"],
        contraindications=["wrist_pain"]
    ),
    Exercise(
        id="ex_incline_dumbbell_press",
        name="Incline Dumbbell Press",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["upper_chest", "anterior_deltoids"],
        secondary_muscles=["triceps"],
        equipment_required=["dumbbells", "bench"],
        instructions="Set bench at 30 degrees. Press dumbbells overhead with wrists stacked over elbows. Lower under control to upper chest line.",
        substitutions=["ex_dumbbell_bench_press", "ex_pushups"],
        contraindications=["shoulder_impingement"]
    ),
    Exercise(
        id="ex_overhead_press",
        name="Barbell Overhead Press (OHP)",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["shoulders", "triceps"],
        secondary_muscles=["upper_chest", "core"],
        equipment_required=["barbell"],
        instructions="Stand tall with bar racked across front deltoids. Squeeze glutes and brace core. Press vertically in a straight path, moving head back then forward at lockout.",
        substitutions=["ex_seated_dumbbell_shoulder_press", "ex_landmine_press"],
        contraindications=["shoulder_impingement", "lower_back_pain"]
    ),
    Exercise(
        id="ex_seated_dumbbell_shoulder_press",
        name="Seated Dumbbell Shoulder Press",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["shoulders", "triceps"],
        secondary_muscles=["upper_chest"],
        equipment_required=["dumbbells", "bench"],
        instructions="Sit supported with dumbbells at ear height, palms facing forward or semi-neutral. Press upwards until arms extend without shrugging trap muscles.",
        substitutions=["ex_lateral_raises", "ex_pushups"],
        contraindications=["shoulder_impingement"]
    ),
    Exercise(
        id="ex_lateral_raises",
        name="Dumbbell Lateral Raises",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["lateral_deltoids"],
        secondary_muscles=["traps"],
        equipment_required=["dumbbells"],
        instructions="Hold light dumbbells at sides. With slight forward torso lean and micro-bend in elbows, sweep arms out to parallel with floor in scapular plane.",
        substitutions=["ex_cable_lateral_raise", "ex_band_lateral_raise"],
        contraindications=[]
    ),
    Exercise(
        id="ex_tricep_dips",
        name="Parallel Bar Dips",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.PRESS,
        primary_muscles=["triceps", "lower_chest"],
        secondary_muscles=["anterior_deltoids"],
        equipment_required=["dip_station"],
        instructions="Support bodyweight on dip bars. Lower body by flexing elbows until upper arms are parallel to floor. Press vigorously back to top.",
        substitutions=["ex_tricep_rope_pushdown", "ex_pushups"],
        contraindications=["shoulder_impingement", "wrist_pain"]
    ),
    Exercise(
        id="ex_tricep_rope_pushdown",
        name="Cable Tricep Rope Pushdown",
        category=ExerciseCategory.PUSH,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["triceps"],
        secondary_muscles=[],
        equipment_required=["cable"],
        instructions="Pin elbows tight at sides. Flex triceps and extend rope downward, flaring rope ends outward at bottom for peak contraction.",
        substitutions=["ex_overhead_dumbbell_tricep_extension", "ex_diamond_pushups"],
        contraindications=["elbow_tendonitis"]
    ),

    # --- BACK / PULL ---
    Exercise(
        id="ex_pullups",
        name="Pull-ups",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.PULLUP,
        primary_muscles=["lats", "upper_back"],
        secondary_muscles=["biceps", "forearms"],
        equipment_required=["pull_up_bar"],
        instructions="Hang from overhead bar with overhand grip wider than shoulders. Depress scapulae and pull chest upward toward bar until chin clears bar.",
        substitutions=["ex_lat_pulldown", "ex_inverted_rows"],
        contraindications=["shoulder_impingement", "elbow_tendonitis"]
    ),
    Exercise(
        id="ex_lat_pulldown",
        name="Lat Pulldown",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.PULLUP,
        primary_muscles=["lats", "biceps"],
        secondary_muscles=["rhomboids", "rear_delts"],
        equipment_required=["cable"],
        instructions="Sit tall with knees locked under pads. Grasp wide bar, lean slightly back (10-15 degrees), and pull smoothly to collarbone while engaging lats.",
        substitutions=["ex_pullups", "ex_resistance_band_pulldown"],
        contraindications=[]
    ),
    Exercise(
        id="ex_barbell_bent_over_row",
        name="Barbell Bent-Over Row",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ROW,
        primary_muscles=["lats", "rhomboids", "middle_traps"],
        secondary_muscles=["biceps", "erector_spinae"],
        equipment_required=["barbell"],
        instructions="Hinge at hips with flat back until torso is 45 degrees. Pull bar toward lower ribs/navel, keeping elbows tucked and squeezing shoulder blades.",
        substitutions=["ex_chest_supported_dumbbell_row", "ex_cable_seated_row"],
        contraindications=["lower_back_pain"]
    ),
    Exercise(
        id="ex_chest_supported_dumbbell_row",
        name="Chest-Supported Dumbbell Row",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ROW,
        primary_muscles=["rhomboids", "lats", "rear_delts"],
        secondary_muscles=["biceps"],
        equipment_required=["dumbbells", "bench"],
        instructions="Lie prone on incline bench (30-45 degrees). Pull dumbbells upward toward hips without hyperextending lower back, completely unloading spinal erectors.",
        substitutions=["ex_cable_seated_row", "ex_one_arm_dumbbell_row"],
        contraindications=[]
    ),
    Exercise(
        id="ex_one_arm_dumbbell_row",
        name="Single-Arm Dumbbell Row",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ROW,
        primary_muscles=["lats", "rhomboids"],
        secondary_muscles=["biceps"],
        equipment_required=["dumbbells", "bench"],
        instructions="Place one knee and hand on flat bench. With free hand, pull dumbbell upward in an arc toward hip pocket, keeping spine in neutral alignment.",
        substitutions=["ex_chest_supported_dumbbell_row", "ex_inverted_rows"],
        contraindications=["lower_back_pain"]
    ),
    Exercise(
        id="ex_cable_seated_row",
        name="Seated Cable Row",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ROW,
        primary_muscles=["rhomboids", "middle_traps", "lats"],
        secondary_muscles=["biceps"],
        equipment_required=["cable"],
        instructions="Sit with slight knee bend and upright chest. Pull close-grip attachment into abdomen while driving elbows backward and squeezing scapulae together.",
        substitutions=["ex_chest_supported_dumbbell_row", "ex_resistance_band_row"],
        contraindications=[]
    ),
    Exercise(
        id="ex_face_pulls",
        name="Cable Face Pulls",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["rear_delts", "rotator_cuff", "rhomboids"],
        secondary_muscles=["traps"],
        equipment_required=["cable"],
        instructions="Attach rope at eye height. Pull rope toward bridge of nose while externally rotating hands back like a double bicep pose. High postural benefit.",
        substitutions=["ex_band_pull_aparts", "ex_rear_delt_flyes"],
        contraindications=[]
    ),
    Exercise(
        id="ex_barbell_bicep_curl",
        name="Barbell Bicep Curl",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["biceps"],
        secondary_muscles=["forearms"],
        equipment_required=["barbell"],
        instructions="Stand shoulder-width with underhand grip. Curl bar upward toward shoulders without swinging elbows or using hip momentum.",
        substitutions=["ex_dumbbell_hammer_curl", "ex_cable_bicep_curl"],
        contraindications=["wrist_pain"]
    ),
    Exercise(
        id="ex_dumbbell_hammer_curl",
        name="Dumbbell Hammer Curl",
        category=ExerciseCategory.PULL,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["brachialis", "biceps", "brachioradialis"],
        secondary_muscles=["forearms"],
        equipment_required=["dumbbells"],
        instructions="Hold dumbbells with neutral (palms facing inward) grip. Curl upward while keeping elbows locked in place.",
        substitutions=["ex_barbell_bicep_curl", "ex_resistance_band_curl"],
        contraindications=[]
    ),

    # --- LEGS / LOWER BODY ---
    Exercise(
        id="ex_barbell_back_squat",
        name="Barbell Back Squat",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.SQUAT,
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["hamstrings", "core", "erector_spinae"],
        equipment_required=["barbell", "squat_rack"],
        instructions="Rest bar on upper traps. Feet shoulder-width, toes angled slightly out. Descend by breaking at hips and knees simultaneously until thighs reach parallel.",
        substitutions=["ex_goblet_squat", "ex_leg_press", "ex_box_squats"],
        contraindications=["lower_back_pain", "knee_pain"]
    ),
    Exercise(
        id="ex_goblet_squat",
        name="Dumbbell Goblet Squat",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.SQUAT,
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["core", "upper_back"],
        equipment_required=["dumbbells"],
        instructions="Cup a single dumbbell vertically against sternum. Squat deep between knees while keeping chest proud and spine tall.",
        substitutions=["ex_bodyweight_squats", "ex_box_squats"],
        contraindications=[]
    ),
    Exercise(
        id="ex_box_squats",
        name="Box Squats",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.SQUAT,
        primary_muscles=["glutes", "quadriceps"],
        secondary_muscles=["hamstrings"],
        equipment_required=["bodyweight", "bench"],
        instructions="Sit back onto a knee-height box or bench with vertical shins, pause for 1 second without rocking, then drive through heels to stand. Highly joint-friendly.",
        substitutions=["ex_goblet_squat", "ex_glute_bridges"],
        contraindications=[]
    ),
    Exercise(
        id="ex_bodyweight_squats",
        name="Bodyweight Air Squats",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.SQUAT,
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["core"],
        equipment_required=["bodyweight"],
        instructions="Arms extended in front. Squat down under control until hips dip parallel, tracking knees over second toes.",
        substitutions=["ex_goblet_squat", "ex_box_squats"],
        contraindications=[]
    ),
    Exercise(
        id="ex_barbell_deadlift",
        name="Conventional Barbell Deadlift",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.HINGE,
        primary_muscles=["hamstrings", "glutes", "erector_spinae"],
        secondary_muscles=["lats", "traps", "forearms"],
        equipment_required=["barbell"],
        instructions="Stand with bar over mid-foot. Hinge down, grip bar just outside shins. Flatten back, push floor away through mid-foot/heels, standing tall without hyperextending.",
        substitutions=["ex_romanian_deadlift", "ex_trap_bar_deadlift", "ex_glute_bridges"],
        contraindications=["lower_back_pain"]
    ),
    Exercise(
        id="ex_romanian_deadlift",
        name="Dumbbell Romanian Deadlift (RDL)",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.HINGE,
        primary_muscles=["hamstrings", "glutes"],
        secondary_muscles=["erector_spinae", "core"],
        equipment_required=["dumbbells"],
        instructions="Hold dumbbells in front of thighs with slight knee softness. Push hips straight back as if touching a wall behind you, sliding weights down shins until hamstrings stretch.",
        substitutions=["ex_glute_bridges", "ex_swiss_ball_hamstring_curls"],
        contraindications=["acute_lower_back_pain"]
    ),
    Exercise(
        id="ex_glute_bridges",
        name="Glute Bridges",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.HINGE,
        primary_muscles=["glutes"],
        secondary_muscles=["hamstrings", "core"],
        equipment_required=["bodyweight"],
        instructions="Lie supine with knees bent and feet flat near hips. Drive through heels to lift hips until hips and knees align. Squeeze glutes hard at top without arching lumbar spine.",
        substitutions=["ex_hip_thrusts", "ex_romanian_deadlift"],
        contraindications=[]
    ),
    Exercise(
        id="ex_walking_lunges",
        name="Dumbbell Walking Lunges",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.LUNGE,
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["hamstrings", "calves", "core"],
        equipment_required=["dumbbells"],
        instructions="Step forward into a lunge, lowering back knee until 1 inch off floor. Push through front heel to step directly into next forward stride.",
        substitutions=["ex_reverse_lunges", "ex_step_ups", "ex_goblet_squat"],
        contraindications=["knee_pain"]
    ),
    Exercise(
        id="ex_reverse_lunges",
        name="Reverse Lunges",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.LUNGE,
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["hamstrings"],
        equipment_required=["bodyweight"],
        instructions="Step backward and lower back knee gently toward floor. Keeps shin more vertical, significantly reducing anterior knee shear stress.",
        substitutions=["ex_box_squats", "ex_glute_bridges"],
        contraindications=[]
    ),
    Exercise(
        id="ex_standing_calf_raise",
        name="Standing Calf Raises",
        category=ExerciseCategory.LEGS,
        movement_pattern=MovementPattern.ISOLATION,
        primary_muscles=["calves"],
        secondary_muscles=[],
        equipment_required=["bodyweight"],
        instructions="Stand on edge of step on balls of feet. Lower heels for a deep calf stretch, then rise onto tiptoes with a 1-second peak squeeze.",
        substitutions=["ex_seated_calf_raise"],
        contraindications=[]
    ),

    # --- CORE / ABDOMINALS ---
    Exercise(
        id="ex_plank",
        name="Standard Forearm Plank",
        category=ExerciseCategory.CORE,
        movement_pattern=MovementPattern.CORE,
        primary_muscles=["transverse_abdominis", "rectus_abdominis"],
        secondary_muscles=["shoulders", "glutes"],
        equipment_required=["bodyweight"],
        instructions="Rest on forearms and toes. Keep spine neutral, squeeze glutes, pull navel toward spine, and hold tension without letting hips sag.",
        substitutions=["ex_deadbug", "ex_bird_dog"],
        contraindications=["acute_lower_back_pain"]
    ),
    Exercise(
        id="ex_deadbug",
        name="Deadbug",
        category=ExerciseCategory.CORE,
        movement_pattern=MovementPattern.CORE,
        primary_muscles=["deep_core", "transverse_abdominis"],
        secondary_muscles=["hip_flexors"],
        equipment_required=["bodyweight"],
        instructions="Lie supine with arms pointing to ceiling and knees at 90 degrees. Press lower back flat into floor. Extend opposite arm and leg slowly, returning to center.",
        substitutions=["ex_bird_dog", "ex_plank"],
        contraindications=[]
    ),
    Exercise(
        id="ex_bird_dog",
        name="Bird Dog",
        category=ExerciseCategory.CORE,
        movement_pattern=MovementPattern.CORE,
        primary_muscles=["multifidus", "erector_spinae", "glutes"],
        secondary_muscles=["core"],
        equipment_required=["bodyweight"],
        instructions="On all fours with hands under shoulders, knees under hips. Reach opposite arm forward and leg straight back until parallel to floor. Hold 2 seconds.",
        substitutions=["ex_deadbug", "ex_plank"],
        contraindications=[]
    ),
    Exercise(
        id="ex_hanging_knee_raises",
        name="Hanging Knee Raises",
        category=ExerciseCategory.CORE,
        movement_pattern=MovementPattern.CORE,
        primary_muscles=["lower_abs", "hip_flexors"],
        secondary_muscles=["forearms"],
        equipment_required=["pull_up_bar"],
        instructions="Hang from bar with active shoulders. Flex hips and curl knees up to chest height without swinging, then lower under control.",
        substitutions=["ex_deadbug", "ex_reverse_crunches"],
        contraindications=["shoulder_impingement", "lower_back_pain"]
    )
]

# Quick indexing
_EXERCISE_MAP: Dict[str, Exercise] = {ex.id: ex for ex in EXERCISE_CATALOG}


def get_exercise_by_id(exercise_id: str) -> Optional[Exercise]:
    """Retrieve an exercise definition by its unique identifier."""
    return _EXERCISE_MAP.get(exercise_id)


def search_exercises(
    query: Optional[str] = None,
    category: Optional[ExerciseCategory] = None,
    movement_pattern: Optional[MovementPattern] = None,
    available_equipment: Optional[List[str]] = None,
    avoid_contraindications: Optional[List[str]] = None,
    limit: int = 20
) -> List[Exercise]:
    """Search and filter exercise database with rigorous safety contraindication avoidance."""
    results: List[Exercise] = []
    
    # Normalize equipment and contraindication sets
    equip_set = set([e.lower().strip() for e in available_equipment]) if available_equipment else None
    if equip_set is not None:
        equip_set.add("bodyweight")  # Bodyweight is always available
        
    avoid_set = set([c.lower().strip() for c in avoid_contraindications]) if avoid_contraindications else set()

    for ex in EXERCISE_CATALOG:
        # 1. Safety Check: Filter out any exercise with matching contraindications
        if avoid_set:
            ex_contra = set([c.lower().strip() for c in ex.contraindications])
            if avoid_set.intersection(ex_contra):
                continue

        # 2. Equipment Check: Must be performable with user's equipment
        if equip_set is not None:
            ex_req = set([eq.lower().strip() for eq in ex.equipment_required])
            if not ex_req.issubset(equip_set):
                continue

        # 3. Category match
        if category and ex.category != category:
            continue

        # 4. Movement pattern match
        if movement_pattern and ex.movement_pattern != movement_pattern:
            continue

        # 5. Text search query match
        if query:
            q = query.lower()
            name_match = q in ex.name.lower()
            muscle_match = any(q in m.lower() for m in ex.primary_muscles + ex.secondary_muscles)
            instr_match = q in ex.instructions.lower()
            if not (name_match or muscle_match or instr_match):
                continue

        results.append(ex)
        if len(results) >= limit:
            break

    return results


def find_safe_substitute(exercise_id: str, avoid_contraindications: List[str], available_equipment: Optional[List[str]] = None) -> Optional[Exercise]:
    """Find the best safe substitute for an exercise when the original is contraindicated or missing equipment."""
    original = get_exercise_by_id(exercise_id)
    if not original:
        return None

    avoid_set = set([c.lower().strip() for c in avoid_contraindications])
    equip_set = set([e.lower().strip() for e in available_equipment]) if available_equipment else None
    if equip_set:
        equip_set.add("bodyweight")

    # First check direct substitution list
    for sub_id in original.substitutions:
        candidate = get_exercise_by_id(sub_id)
        if candidate:
            cand_contra = set([c.lower().strip() for c in candidate.contraindications])
            if not avoid_set.intersection(cand_contra):
                if equip_set is None or set(candidate.equipment_required).issubset(equip_set):
                    return candidate

    # Fallback: search by movement pattern or category
    fallbacks = search_exercises(
        category=original.category,
        movement_pattern=original.movement_pattern,
        available_equipment=available_equipment,
        avoid_contraindications=avoid_contraindications,
        limit=5
    )
    return fallbacks[0] if fallbacks else None
