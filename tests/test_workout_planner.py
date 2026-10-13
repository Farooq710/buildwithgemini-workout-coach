"""Tests for workout plan generation and split balance."""

import pytest
from workout_coach.core.workout_planner import WorkoutPlanner
from workout_coach.core.models import FitnessGoal, ExperienceLevel, FitnessProfile
from workout_coach.core.safety import validate_plan_safety


def test_generate_plan_full_body(sample_profile):
    """Verify 3-day beginner profile generates balanced sessions with warm-up and cooldown."""
    sample_profile.experience_level = ExperienceLevel.BEGINNER
    plan = WorkoutPlanner.generate_plan(sample_profile)
    assert plan.user_id == sample_profile.user_id
    assert len(plan.sessions) == 3
    for s in plan.sessions:
        assert len(s.exercises) >= 3
        assert len(s.warm_up) > 0
        assert len(s.cooldown) > 0


def test_generate_plan_avoids_contraindications(injured_profile):
    """Verify that generated plan for user with lower back pain and shoulder impingement has zero unsafe exercises."""
    plan = WorkoutPlanner.generate_plan(injured_profile)
    is_safe, violations = validate_plan_safety(plan, injured_profile)
    assert is_safe, f"Generated plan violated safety: {violations}"
    
    # Check no exercise in plan contains the contraindicated IDs
    for s in plan.sessions:
        for ex in s.exercises:
            assert ex.exercise_id not in ["ex_barbell_deadlift", "ex_barbell_bent_over_row", "ex_overhead_press"]


def test_generate_plan_upper_lower():
    """Verify 4-day profile generates Upper/Lower split."""
    profile = FitnessProfile(
        user_id="user_4day",
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
        experience_level=ExperienceLevel.INTERMEDIATE,
        available_equipment=["dumbbells", "barbell", "bench"],
        days_per_week=4,
        session_duration_minutes=60
    )
    plan = WorkoutPlanner.generate_plan(profile)
    assert plan.split_type == "upper_lower"
    assert len(plan.sessions) == 4
