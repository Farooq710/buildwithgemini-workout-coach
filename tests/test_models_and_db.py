"""Tests for domain models, database schema, and repository persistence."""

import pytest
from datetime import date
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel,
    CompletedSession,
    CompletedExercise,
    CompletedSet
)


def test_profile_persistence(repo, sample_profile):
    """Verify profile can be saved, retrieved, and updated in database."""
    saved = repo.save_profile(sample_profile)
    assert saved.user_id == sample_profile.user_id

    retrieved = repo.get_profile(sample_profile.user_id)
    assert retrieved is not None
    assert retrieved.fitness_goal == FitnessGoal.STRENGTH
    assert retrieved.days_per_week == 3
    assert "barbell" in retrieved.available_equipment


def test_workout_session_and_sets_persistence(repo, sample_profile):
    """Verify completed session with set-level telemetry is transactionally persisted."""
    repo.save_profile(sample_profile)

    session = CompletedSession(
        id="test_sess_001",
        user_id=sample_profile.user_id,
        session_date=date.today(),
        duration_minutes=50,
        perceived_effort_rpe=8,
        exercises=[
            CompletedExercise(
                exercise_id="ex_barbell_bench_press",
                exercise_name="Barbell Bench Press",
                sets=[
                    CompletedSet(set_number=1, weight_kg=80.0, reps_performed=8, rpe=7),
                    CompletedSet(set_number=2, weight_kg=80.0, reps_performed=8, rpe=8),
                    CompletedSet(set_number=3, weight_kg=82.5, reps_performed=6, rpe=9),
                ]
            )
        ],
        feedback="Felt strong on bench press today."
    )

    saved = repo.save_completed_session(session)
    assert saved.id == "test_sess_001"

    sessions = repo.get_completed_sessions(sample_profile.user_id)
    assert len(sessions) == 1
    assert sessions[0].duration_minutes == 50
    assert len(sessions[0].exercises[0].sets) == 3

    # Check sets table queries
    sets_history = repo.get_exercise_sets_history(sample_profile.user_id, "ex_barbell_bench_press")
    assert len(sets_history) == 3
    assert sets_history[0]["weight_kg"] == 80.0
    assert sets_history[2]["weight_kg"] == 82.5
