#!/usr/bin/env python3
"""Standalone End-to-End CLI Demo for AI Workout Coach with Cloud Firestore."""

import os
import sys
import json
from datetime import date

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from workout_coach.core.repository_factory import get_repository
from workout_coach.agent.tools import WorkoutCoachTools
from workout_coach.agent.coach import WorkoutCoach
from workout_coach.agent.model_adapter import MockWorkoutCoachModelAdapter


def run_demo():
    print("=" * 70)
    print("  🏋️‍♂️  AI WORKOUT COACH — END-TO-END DEMO WITH CLOUD FIRESTORE")
    print("=" * 70)

    # Initialize repository (Cloud Firestore or SQLite)
    repo = get_repository()
    print(f"📦 Active Storage Backend: {repo.__class__.__name__}")
    if hasattr(repo, "seed_exercises"):
        repo.seed_exercises()

    tools = WorkoutCoachTools(repo)
    coach = WorkoutCoach(repo=repo, model_adapter=MockWorkoutCoachModelAdapter())

    user_id = "athlete_demo_alex"

    # Step 1: Onboard Athlete Profile
    print("\n[STEP 1] Onboarding Athlete Profile (with declared injury limitation)...")
    profile_turn = coach.process_message(
        user_id=user_id,
        message="Hi! I want to build strength with dumbbells, barbell, and bench for 3 days a week. Note that I have lower back pain."
    )
    print(f"Coach Reply: {profile_turn.reply}")
    profile = repo.get_profile(user_id)
    print(f"Stored Profile: Goal={profile.fitness_goal.value}, Days={profile.days_per_week}, Equipment={profile.available_equipment}, Limitations={profile.limitations}")

    # Step 2: Generate Customized Workout Plan
    print("\n[STEP 2] Generating Customized Workout Plan & Validating Safety...")
    plan_turn = coach.process_message(
        user_id=user_id,
        message="Please generate my workout plan"
    )
    print(f"Coach Reply: {plan_turn.reply}")
    plan = repo.get_current_workout_plan(user_id)
    print(f"\nActive Plan: '{plan.plan_name}' ({plan.split_type})")
    for s in plan.sessions:
        print(f"  • {s.day_name}: {s.focus}")
        for e in s.exercises:
            print(f"    - {e.exercise_name}: {e.target_sets} sets x {e.target_reps} reps (Rest {e.rest_seconds}s)")

    # Step 3: Search Safe Exercises
    print("\n[STEP 3] Search Exercise Library with Contraindication Avoidance...")
    safe_search = tools.search_exercises(
        category="legs",
        equipment=["dumbbells"],
        avoid_contraindications=["lower_back_pain"]
    )
    print(f"Found {safe_search['count']} safe leg movements avoiding lower back pain:")
    for ex in safe_search["exercises"][:3]:
        print(f"  • {ex['name']} ({ex['movement_pattern']}) - Cues: {ex['instructions'][:80]}...")

    # Step 4: Log a Completed Workout Session
    print("\n[STEP 4] Logging Completed Workout Session with Set-Level Telemetry...")
    session_data = {
        "duration_minutes": 50,
        "perceived_effort_rpe": 7,
        "exercises": [
            {
                "exercise_id": "ex_dumbbell_bench_press",
                "exercise_name": "Dumbbell Bench Press",
                "sets": [
                    {"set_number": 1, "weight_kg": 24.0, "reps_performed": 8, "rpe": 7},
                    {"set_number": 2, "weight_kg": 24.0, "reps_performed": 8, "rpe": 7},
                    {"set_number": 3, "weight_kg": 26.0, "reps_performed": 6, "rpe": 8}
                ]
            },
            {
                "exercise_id": "ex_goblet_squat",
                "exercise_name": "Dumbbell Goblet Squat",
                "sets": [
                    {"set_number": 1, "weight_kg": 28.0, "reps_performed": 10, "rpe": 7},
                    {"set_number": 2, "weight_kg": 28.0, "reps_performed": 10, "rpe": 8}
                ]
            }
        ],
        "feedback": "Felt solid and controlled. Lower back had zero discomfort."
    }
    log_res = tools.log_workout_session(user_id, session_data)
    print(f"Session Logged: status={log_res['status']}, session_id={log_res['session_id']}")

    # Step 5: Deterministic Progress & Progressive Overload Analytics
    print("\n[STEP 5] Querying Deterministic Progress Analytics...")
    prog_turn = coach.process_message(
        user_id=user_id,
        message="What is my progress and volume so far?"
    )
    print(f"Coach Reply: {prog_turn.reply}")

    # Step 6: Testing Safety Red-Flag Interception
    print("\n[STEP 6] Testing Safety Red-Flag Guardrail Interception...")
    red_flag_turn = coach.process_message(
        user_id=user_id,
        message="I felt a sudden sharp pain and popping sound in my shoulder during bench press."
    )
    print(f"Coach Reply:\n{red_flag_turn.reply}")

    print("\n" + "=" * 70)
    print(f"  ✅ DEMO COMPLETE: Stored in {repo.__class__.__name__} with zero errors!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
