"""Tests for safety interceptors, medical red flags, and contraindication validation."""

import pytest
from workout_coach.core.safety import scan_for_red_flags, validate_plan_safety
from workout_coach.core.models import WorkoutPlan, PlannedSession, PlannedExercise, FitnessGoal


def test_red_flag_chest_pain():
    """Verify red flag detection for chest pain symptoms."""
    msg = "I was doing bench press and started feeling sudden chest pain and shortness of breath."
    warning = scan_for_red_flags(msg)
    assert warning is not None
    assert "SAFETY ALERT" in warning
    assert "healthcare professional" in warning


def test_red_flag_dizziness():
    """Verify red flag detection for dizziness or lightheadedness."""
    msg = "After that heavy squat I am feeling dizzy and passed out almost."
    warning = scan_for_red_flags(msg)
    assert warning is not None
    assert "SAFETY ALERT" in warning


def test_normal_muscle_soreness_not_flagged():
    """Verify regular delayed-onset muscle soreness does not trigger false-positive red flags."""
    msg = "My chest is really sore and tight from yesterday's workout, what should I do?"
    warning = scan_for_red_flags(msg)
    assert warning is None


def test_validate_plan_safety_detects_contraindication(injured_profile):
    """Verify plan validator catches a manually injected contraindicated exercise."""
    # Inject Barbell Deadlift into a plan for a user with lower back pain
    unsafe_plan = WorkoutPlan(
        id="unsafe_01",
        user_id=injured_profile.user_id,
        plan_name="Unsafe Plan",
        goal=FitnessGoal.STRENGTH,
        split_type="full_body",
        days_per_week=1,
        sessions=[
            PlannedSession(
                day_number=1,
                day_name="Day 1",
                focus="Legs",
                exercises=[
                    PlannedExercise(
                        exercise_id="ex_barbell_deadlift",
                        exercise_name="Conventional Barbell Deadlift",
                        order_in_session=1,
                        target_sets=3,
                        target_reps="5",
                        rest_seconds=120
                    )
                ]
            )
        ],
        rationale="Testing safety validator"
    )

    is_safe, violations = validate_plan_safety(unsafe_plan, injured_profile)
    assert not is_safe
    assert any("lower_back_pain" in v for v in violations)
