"""Tests for Google Cloud Firestore persistent repository."""

import pytest
import os
from datetime import date
from workout_coach.core.firestore_repository import FirestoreWorkoutRepository
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel,
    WorkoutPlan,
    PlannedSession,
    PlannedExercise,
    CompletedSession,
    CompletedExercise,
    CompletedSet
)

PROJECT_ID = "qwiklabs-gcp-04-9ecf92a8e298"


@pytest.fixture
def firestore_repo():
    return FirestoreWorkoutRepository(project_id=PROJECT_ID)


def test_firestore_profile_crud(firestore_repo):
    """Verify saving and retrieving athlete profile from Cloud Firestore."""
    user_id = "test_firestore_user_01"
    profile = FitnessProfile(
        user_id=user_id,
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
        experience_level=ExperienceLevel.BEGINNER,
        available_equipment=["dumbbells", "bench"],
        days_per_week=3,
        session_duration_minutes=45,
        limitations=["shoulder_impingement"]
    )

    saved = firestore_repo.save_profile(profile)
    assert saved.user_id == user_id

    fetched = firestore_repo.get_profile(user_id)
    assert fetched is not None
    assert fetched.fitness_goal == FitnessGoal.MUSCLE_GAIN
    assert "shoulder_impingement" in fetched.limitations

    all_profiles = firestore_repo.list_profiles()
    assert isinstance(all_profiles, list)
    assert any(p.user_id == user_id for p in all_profiles)


def test_firestore_workout_plan_crud(firestore_repo):
    """Verify saving and retrieving active workout plan from Cloud Firestore."""
    user_id = "test_firestore_user_02"
    plan = WorkoutPlan(
        id="test_plan_fs_01",
        user_id=user_id,
        plan_name="Firestore Test Split",
        goal=FitnessGoal.GENERAL_FITNESS,
        split_type="full_body",
        days_per_week=3,
        sessions=[
            PlannedSession(
                day_number=1,
                day_name="Day 1",
                focus="Full Body",
                exercises=[
                    PlannedExercise(
                        exercise_id="ex_goblet_squat",
                        exercise_name="Dumbbell Goblet Squat",
                        order_in_session=1,
                        target_sets=3,
                        target_reps="10",
                        rest_seconds=90
                    )
                ]
            )
        ],
        rationale="Testing Cloud Firestore persistence"
    )

    firestore_repo.save_workout_plan(plan)
    active_plan = firestore_repo.get_current_workout_plan(user_id)
    assert active_plan is not None
    assert active_plan.id == "test_plan_fs_01"
    assert len(active_plan.sessions) == 1


def test_firestore_session_and_sets_crud(firestore_repo):
    """Verify saving and querying session logs with set telemetry in Cloud Firestore."""
    user_id = "test_firestore_user_03"
    session = CompletedSession(
        id="test_sess_fs_01",
        user_id=user_id,
        session_date=date.today(),
        duration_minutes=45,
        perceived_effort_rpe=7,
        exercises=[
            CompletedExercise(
                exercise_id="ex_pushups",
                exercise_name="Push-ups",
                sets=[
                    CompletedSet(set_number=1, weight_kg=0.0, reps_performed=15, rpe=7),
                    CompletedSet(set_number=2, weight_kg=0.0, reps_performed=12, rpe=8)
                ]
            )
        ],
        feedback="Felt good, solid chest pump."
    )

    firestore_repo.save_completed_session(session)
    sessions = firestore_repo.get_completed_sessions(user_id)
    assert len(sessions) >= 1
    assert sessions[0].id == "test_sess_fs_01"

    sets_history = firestore_repo.get_exercise_sets_history(user_id, "ex_pushups")
    assert len(sets_history) >= 2
    assert sets_history[0]["reps_performed"] == 15
