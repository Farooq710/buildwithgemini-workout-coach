"""End-to-end integration test demonstrating the complete 5-step user journey."""

import pytest
from datetime import date
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel
)


def test_complete_e2e_user_journey(coach, tools, repo):
    """Demonstrate the entire end-to-end user lifecycle from profile to progressive overload."""
    user_id = "athlete_e2e_sarah"

    # Step 1: User creates fitness profile
    profile_turn = coach.process_message(
        user_id=user_id,
        message="Hi, I want to build strength using dumbbells and a bench, training 3 days a week. Note that I have lower back pain."
    )
    assert profile_turn.intent == "update_profile"
    assert "strength" in profile_turn.reply.lower()

    profile = repo.get_profile(user_id)
    assert profile is not None
    assert profile.fitness_goal == FitnessGoal.STRENGTH
    assert "lower_back_pain" in profile.limitations

    # Step 2: Agent generates personalized, safety-verified workout plan
    plan_turn = coach.process_message(
        user_id=user_id,
        message="Please generate my workout plan"
    )
    assert plan_turn.intent == "create_plan"
    plan = repo.get_current_workout_plan(user_id)
    assert plan is not None
    assert plan.days_per_week == 3
    
    # Verify no contraindicated exercises were generated
    for session in plan.sessions:
        for ex in session.exercises:
            assert ex.exercise_id not in ["ex_barbell_deadlift", "ex_barbell_bent_over_row"]

    # Step 3: User logs completed workout session with set-level telemetry
    session_data = {
        "duration_minutes": 45,
        "perceived_effort_rpe": 6,
        "exercises": [
            {
                "exercise_id": "ex_dumbbell_bench_press",
                "exercise_name": "Dumbbell Bench Press",
                "sets": [
                    {"set_number": 1, "weight_kg": 16.0, "reps_performed": 10, "rpe": 6},
                    {"set_number": 2, "weight_kg": 16.0, "reps_performed": 10, "rpe": 6},
                    {"set_number": 3, "weight_kg": 16.0, "reps_performed": 10, "rpe": 7}
                ]
            },
            {
                "exercise_id": "ex_goblet_squat",
                "exercise_name": "Dumbbell Goblet Squat",
                "sets": [
                    {"set_number": 1, "weight_kg": 20.0, "reps_performed": 10, "rpe": 6},
                    {"set_number": 2, "weight_kg": 20.0, "reps_performed": 10, "rpe": 6}
                ]
            }
        ],
        "feedback": "Felt comfortable, movements were smooth."
    }
    log_res = tools.log_workout_session(user_id, session_data)
    assert log_res["status"] == "success"

    # Step 4: User queries progress and gets deterministic calculation
    progress_turn = coach.process_message(
        user_id=user_id,
        message="Can you check my progress and volume so far?"
    )
    assert progress_turn.intent == "calculate_progress"
    expected_vol = (16.0 * 10 * 3) + (20.0 * 10 * 2) # 480 + 400 = 880.0 kg
    assert f"{expected_vol:.1f}kg" in progress_turn.reply or "880" in progress_turn.reply

    # Step 5: Safety Guardrail Interception
    urgent_turn = coach.process_message(
        user_id=user_id,
        message="During my last set I felt a sudden sharp pain and popping sound in my shoulder."
    )
    assert urgent_turn.safety_warning is not None
    assert "SAFETY ALERT" in urgent_turn.reply
    assert "STOP exercising immediately" in urgent_turn.reply
