"""Algorithmic workout plan generation engine."""

import uuid
from typing import List, Optional, Tuple
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel,
    WorkoutPlan,
    PlannedSession,
    PlannedExercise,
    ExerciseCategory,
    MovementPattern
)
from workout_coach.core.exercise_library import (
    search_exercises,
    get_exercise_by_id,
    find_safe_substitute
)
from workout_coach.core.safety import validate_plan_safety


class WorkoutPlanner:
    """Generates structured, balanced, and safety-verified training programs."""

    @staticmethod
    def generate_plan(profile: FitnessProfile, plan_name: Optional[str] = None) -> WorkoutPlan:
        """Create a complete customized workout plan tailored to the user's goals and restrictions."""
        days = profile.days_per_week
        goal = profile.fitness_goal
        level = profile.experience_level
        equipment = profile.available_equipment
        limitations = profile.limitations

        # Determine split type
        if days <= 2:
            split_type = "full_body"
            sessions = WorkoutPlanner._build_full_body_split(days, goal, level, equipment, limitations)
        elif days == 3:
            split_type = "push_pull_legs" if level in [ExperienceLevel.INTERMEDIATE, ExperienceLevel.ADVANCED] else "full_body"
            if split_type == "push_pull_legs":
                sessions = WorkoutPlanner._build_ppl_split(3, goal, level, equipment, limitations)
            else:
                sessions = WorkoutPlanner._build_full_body_split(3, goal, level, equipment, limitations)
        elif days == 4:
            split_type = "upper_lower"
            sessions = WorkoutPlanner._build_upper_lower_split(4, goal, level, equipment, limitations)
        else:
            split_type = "push_pull_legs"
            sessions = WorkoutPlanner._build_ppl_split(days, goal, level, equipment, limitations)

        # Formulate rationale
        rationale = (
            f"Designed a {split_type.replace('_', ' ').title()} program across {days} days/week "
            f"optimized for {goal.value.replace('_', ' ')}. Volume is calibrated for {level.value} level "
            f"using available equipment ({', '.join(equipment)}). "
        )
        if limitations:
            rationale += f"Strictly filtered out exercises contraindicated for declared limitation(s): {', '.join(limitations)}."
        else:
            rationale += "Includes full compound progression."

        name = plan_name or f"{level.value.capitalize()} {goal.value.replace('_', ' ').capitalize()} Plan"

        plan = WorkoutPlan(
            id=f"plan_{uuid.uuid4().hex[:10]}",
            user_id=profile.user_id,
            plan_name=name,
            goal=goal,
            split_type=split_type,
            days_per_week=days,
            sessions=sessions,
            rationale=rationale,
            is_active=True
        )

        # Safety verification
        is_safe, violations = validate_plan_safety(plan, profile)
        if not is_safe:
            # If any violation occurred, substitute the problematic exercises
            plan = WorkoutPlanner._remediate_plan_violations(plan, profile, violations)

        return plan

    @staticmethod
    def _get_reps_and_rest(goal: FitnessGoal, pattern: MovementPattern) -> Tuple[int, str, int]:
        """Returns (target_sets, target_reps, rest_seconds)."""
        is_compound = pattern in [MovementPattern.PRESS, MovementPattern.ROW, MovementPattern.SQUAT, MovementPattern.HINGE, MovementPattern.PULLUP]

        if goal == FitnessGoal.STRENGTH:
            if is_compound:
                return 4, "4-6", 150
            return 3, "6-8", 90
        elif goal == FitnessGoal.MUSCLE_GAIN:
            if is_compound:
                return 3, "8-10", 90
            return 3, "10-12", 60
        elif goal == FitnessGoal.ENDURANCE:
            return 3, "12-15", 45
        else:  # General fitness & weight management
            if is_compound:
                return 3, "8-10", 75
            return 3, "10-12", 60

    @staticmethod
    def _build_full_body_split(
        days: int,
        goal: FitnessGoal,
        level: ExperienceLevel,
        equipment: List[str],
        limitations: List[str]
    ) -> List[PlannedSession]:
        sessions = []
        for d in range(1, days + 1):
            # Select 1 squat/leg, 1 push, 1 pull, 1 core
            leg_ex = search_exercises(category=ExerciseCategory.LEGS, available_equipment=equipment, avoid_contraindications=limitations, limit=3)
            push_ex = search_exercises(category=ExerciseCategory.PUSH, available_equipment=equipment, avoid_contraindications=limitations, limit=3)
            pull_ex = search_exercises(category=ExerciseCategory.PULL, available_equipment=equipment, avoid_contraindications=limitations, limit=3)
            core_ex = search_exercises(category=ExerciseCategory.CORE, available_equipment=equipment, avoid_contraindications=limitations, limit=3)

            planned_exercises = []
            order = 1
            # Round-robin selection across days
            candidates = [
                leg_ex[(d - 1) % len(leg_ex)] if leg_ex else None,
                push_ex[(d - 1) % len(push_ex)] if push_ex else None,
                pull_ex[(d - 1) % len(pull_ex)] if pull_ex else None,
                core_ex[(d - 1) % len(core_ex)] if core_ex else None,
            ]
            for cand in candidates:
                if cand:
                    sets, reps, rest = WorkoutPlanner._get_reps_and_rest(goal, cand.movement_pattern)
                    planned_exercises.append(PlannedExercise(
                        exercise_id=cand.id,
                        exercise_name=cand.name,
                        order_in_session=order,
                        target_sets=sets,
                        target_reps=reps,
                        rest_seconds=rest,
                        notes=cand.instructions[:120] + "..."
                    ))
                    order += 1

            sessions.append(PlannedSession(
                day_number=d,
                day_name=f"Day {d} — Full Body",
                focus="Full Body Strength & Conditioning",
                exercises=planned_exercises,
                warm_up=["5 min light brisk walk or jumping jacks", "Arm circles and leg swings (10 each)", "1 set bodyweight squats"],
                cooldown=["Hamstring stretch (30s per leg)", "Doorway chest stretch (30s)", "Deep nasal breathing (2 mins)"]
            ))
        return sessions

    @staticmethod
    def _build_ppl_split(
        days: int,
        goal: FitnessGoal,
        level: ExperienceLevel,
        equipment: List[str],
        limitations: List[str]
    ) -> List[PlannedSession]:
        sessions = []
        cycle = [
            ("Push Focus (Chest, Shoulders, Triceps)", ExerciseCategory.PUSH),
            ("Pull Focus (Back, Biceps, Rear Delts)", ExerciseCategory.PULL),
            ("Legs & Core Focus (Quads, Hamstrings, Glutes)", ExerciseCategory.LEGS)
        ]

        for d in range(1, days + 1):
            title, cat = cycle[(d - 1) % len(cycle)]
            ex_list = search_exercises(category=cat, available_equipment=equipment, avoid_contraindications=limitations, limit=6)
            planned_exercises = []
            order = 1
            for ex in ex_list[:4]:  # Top 4 balanced movements
                sets, reps, rest = WorkoutPlanner._get_reps_and_rest(goal, ex.movement_pattern)
                planned_exercises.append(PlannedExercise(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    order_in_session=order,
                    target_sets=sets,
                    target_reps=reps,
                    rest_seconds=rest,
                    notes=ex.instructions[:120] + "..."
                ))
                order += 1

            # In leg day, add a core movement
            if cat == ExerciseCategory.LEGS:
                core_list = search_exercises(category=ExerciseCategory.CORE, available_equipment=equipment, avoid_contraindications=limitations, limit=1)
                if core_list:
                    c = core_list[0]
                    planned_exercises.append(PlannedExercise(
                        exercise_id=c.id,
                        exercise_name=c.name,
                        order_in_session=order,
                        target_sets=3,
                        target_reps="45s hold" if "plank" in c.id else "12-15",
                        rest_seconds=45,
                        notes=c.instructions[:120] + "..."
                    ))

            sessions.append(PlannedSession(
                day_number=d,
                day_name=f"Day {d} — {title.split(' ')[0]}",
                focus=title,
                exercises=planned_exercises,
                warm_up=["5 min dynamic warm-up", "Scapular retractions and shoulder mobility"],
                cooldown=["Targeted static stretch for worked muscles (3-5 mins)"]
            ))
        return sessions

    @staticmethod
    def _build_upper_lower_split(
        days: int,
        goal: FitnessGoal,
        level: ExperienceLevel,
        equipment: List[str],
        limitations: List[str]
    ) -> List[PlannedSession]:
        sessions = []
        cycle = ["Upper Body", "Lower Body & Core"]
        for d in range(1, days + 1):
            split_name = cycle[(d - 1) % 2]
            planned_exercises = []
            order = 1
            if "Upper" in split_name:
                pushes = search_exercises(category=ExerciseCategory.PUSH, available_equipment=equipment, avoid_contraindications=limitations, limit=2)
                pulls = search_exercises(category=ExerciseCategory.PULL, available_equipment=equipment, avoid_contraindications=limitations, limit=2)
                selected = pushes + pulls
            else:
                legs = search_exercises(category=ExerciseCategory.LEGS, available_equipment=equipment, avoid_contraindications=limitations, limit=3)
                cores = search_exercises(category=ExerciseCategory.CORE, available_equipment=equipment, avoid_contraindications=limitations, limit=1)
                selected = legs + cores

            for ex in selected:
                sets, reps, rest = WorkoutPlanner._get_reps_and_rest(goal, ex.movement_pattern)
                planned_exercises.append(PlannedExercise(
                    exercise_id=ex.id,
                    exercise_name=ex.name,
                    order_in_session=order,
                    target_sets=sets,
                    target_reps=reps,
                    rest_seconds=rest,
                    notes=ex.instructions[:120] + "..."
                ))
                order += 1

            sessions.append(PlannedSession(
                day_number=d,
                day_name=f"Day {d} — {split_name}",
                focus=f"Balanced {split_name} Development",
                exercises=planned_exercises,
                warm_up=["5 min dynamic mobility routine"],
                cooldown=["Full body cool-down stretching"]
            ))
        return sessions

    @staticmethod
    def _remediate_plan_violations(
        plan: WorkoutPlan,
        profile: FitnessProfile,
        violations: List[str]
    ) -> WorkoutPlan:
        """Replace any violating exercises with safe substitutes."""
        remediated_sessions = []
        for session in plan.sessions:
            remediated_exs = []
            for pe in session.exercises:
                ex_def = get_exercise_by_id(pe.exercise_id)
                needs_replace = False
                if ex_def:
                    clashes = set(profile.limitations).intersection(set(ex_def.contraindications))
                    missing = set(ex_def.equipment_required) - set(profile.available_equipment + ["bodyweight"])
                    if clashes or missing:
                        needs_replace = True

                if needs_replace:
                    sub = find_safe_substitute(pe.exercise_id, profile.limitations, profile.available_equipment)
                    if sub:
                        pe = PlannedExercise(
                            exercise_id=sub.id,
                            exercise_name=sub.name,
                            order_in_session=pe.order_in_session,
                            target_sets=pe.target_sets,
                            target_reps=pe.target_reps,
                            rest_seconds=pe.rest_seconds,
                            notes=f"Substituted for safety. {sub.instructions[:100]}..."
                        )
                remediated_exs.append(pe)
            session.exercises = remediated_exs
            remediated_sessions.append(session)

        plan.sessions = remediated_sessions
        return plan
