"""Tests for all 9 core agent tools and their persistence verification."""

import pytest


def test_tool_1_and_2_profile_tools(tools):
    """Test Tool 1 (get_fitness_profile) and Tool 2 (update_fitness_profile)."""
    # 1. Non-existent profile
    res1 = tools.get_fitness_profile("u_tool_test")
    assert res1["status"] == "not_found"

    # 2. Update/create profile
    res2 = tools.update_fitness_profile(
        user_id="u_tool_test",
        fitness_goal="strength",
        experience_level="intermediate",
        available_equipment=["dumbbells", "bench"],
        days_per_week=3,
        limitations=["lower_back_pain"]
    )
    assert res2["status"] == "success"
    assert res2["profile"]["fitness_goal"] == "strength"

    # 3. Retrieve verified
    res3 = tools.get_fitness_profile("u_tool_test")
    assert res3["status"] == "success"
    assert res3["profile"]["days_per_week"] == 3


def test_tool_3_and_4_plan_tools(tools):
    """Test Tool 3 (create_workout_plan) and Tool 4 (get_current_workout_plan)."""
    tools.update_fitness_profile(
        user_id="u_plan_test",
        fitness_goal="muscle_gain",
        available_equipment=["dumbbells", "bodyweight"],
        days_per_week=3
    )

    # Generate plan
    res_plan = tools.create_workout_plan("u_plan_test")
    assert res_plan["status"] == "success"
    assert "plan" in res_plan

    # Retrieve current plan
    res_curr = tools.get_current_workout_plan("u_plan_test")
    assert res_curr["status"] == "success"
    assert res_curr["plan"]["days_per_week"] == 3


def test_tool_5_search_exercises(tools):
    """Test Tool 5 (search_exercises)."""
    res = tools.search_exercises(query="squat")
    assert res["status"] == "success"
    assert res["count"] > 0
    assert any("Squat" in ex["name"] for ex in res["exercises"])


def test_tool_6_and_7_logging_and_history_tools(tools):
    """Test Tool 6 (log_workout_session) and Tool 7 (get_workout_history)."""
    tools.update_fitness_profile(user_id="u_log_test", days_per_week=3)

    session_payload = {
        "duration_minutes": 40,
        "perceived_effort_rpe": 7,
        "exercises": [
            {
                "exercise_id": "ex_pushups",
                "exercise_name": "Push-ups",
                "sets": [
                    {"set_number": 1, "weight_kg": 0.0, "reps_performed": 15, "rpe": 7},
                    {"set_number": 2, "weight_kg": 0.0, "reps_performed": 12, "rpe": 8}
                ]
            }
        ],
        "feedback": "Felt good and brisk."
    }

    log_res = tools.log_workout_session("u_log_test", session_payload)
    assert log_res["status"] == "success"
    assert log_res["exercises_logged"] == 1

    hist_res = tools.get_workout_history("u_log_test")
    assert hist_res["status"] == "success"
    assert hist_res["count"] == 1
    assert hist_res["sessions"][0]["duration_minutes"] == 40


def test_tool_8_and_9_progress_and_adjustment_tools(tools):
    """Test Tool 8 (calculate_progress) and Tool 9 (suggest_workout_adjustment)."""
    tools.update_fitness_profile(user_id="u_prog_test", days_per_week=3)

    session_payload = {
        "duration_minutes": 45,
        "perceived_effort_rpe": 5,
        "exercises": [
            {
                "exercise_id": "ex_dumbbell_bench_press",
                "exercise_name": "Dumbbell Bench Press",
                "sets": [
                    {"set_number": 1, "weight_kg": 20.0, "reps_performed": 10, "rpe": 5}
                ]
            }
        ],
        "feedback": "Felt too easy."
    }
    tools.log_workout_session("u_prog_test", session_payload)

    # Tool 8: Calculate progress
    prog_res = tools.calculate_progress("u_prog_test")
    assert prog_res["status"] == "success"
    assert prog_res["metrics"]["total_volume_kg"] == 200.0

    # Tool 9: Suggest adjustment
    adj_res = tools.suggest_workout_adjustment("u_prog_test", session_feedback="Felt too easy")
    assert adj_res["status"] == "success"
    assert any("Add 2.5kg" in a or "reps" in a for a in adj_res["suggested_adjustments"])
