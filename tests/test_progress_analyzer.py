"""Tests for deterministic fitness mathematics, 1RM estimates, and volume calculations."""

import pytest
from datetime import date, timedelta
from workout_coach.core.models import (
    CompletedSession,
    CompletedExercise,
    CompletedSet
)
from workout_coach.core.progress_analyzer import (
    calculate_epley_1rm,
    calculate_session_volume,
    ProgressAnalyzer
)


def test_epley_1rm_math():
    """Verify Epley 1RM formula calculation."""
    # 100kg for 1 rep = 100kg
    assert calculate_epley_1rm(100.0, 1) == 100.0
    # 100kg for 10 reps = 100 * (1 + 10/30) = 133.3kg
    assert calculate_epley_1rm(100.0, 10) == 133.3
    # 0 weight or 0 reps returns 0.0
    assert calculate_epley_1rm(0.0, 10) == 0.0
    assert calculate_epley_1rm(100.0, 0) == 0.0


def test_session_volume_calculation():
    """Verify sum of sets * reps * weight."""
    session = CompletedSession(
        id="s1",
        user_id="u1",
        session_date=date.today(),
        duration_minutes=45,
        exercises=[
            CompletedExercise(
                exercise_id="ex1",
                exercise_name="Bench Press",
                sets=[
                    CompletedSet(set_number=1, weight_kg=50.0, reps_performed=10), # 500
                    CompletedSet(set_number=2, weight_kg=50.0, reps_performed=10), # 500
                ]
            ),
            CompletedExercise(
                exercise_id="ex2",
                exercise_name="Squat",
                sets=[
                    CompletedSet(set_number=1, weight_kg=100.0, reps_performed=5), # 500
                ]
            )
        ]
    )
    # Total volume = 500 + 500 + 500 = 1500.0 kg
    assert calculate_session_volume(session) == 1500.0


def test_progress_analyzer_progression(sample_profile):
    """Verify that multiple logged sessions calculate adherence and progressive overload correctly."""
    # Session 1: 50kg for 8 reps (e1RM = 63.3)
    s1 = CompletedSession(
        id="s1",
        user_id=sample_profile.user_id,
        session_date=date.today() - timedelta(days=5),
        duration_minutes=45,
        perceived_effort_rpe=7,
        exercises=[
            CompletedExercise(
                exercise_id="ex_barbell_bench_press",
                exercise_name="Barbell Bench Press",
                sets=[CompletedSet(set_number=1, weight_kg=50.0, reps_performed=8)]
            )
        ]
    )

    # Session 2: 55kg for 8 reps (e1RM = 69.7 -> increasing trend)
    s2 = CompletedSession(
        id="s2",
        user_id=sample_profile.user_id,
        session_date=date.today() - timedelta(days=1),
        duration_minutes=45,
        perceived_effort_rpe=6,
        exercises=[
            CompletedExercise(
                exercise_id="ex_barbell_bench_press",
                exercise_name="Barbell Bench Press",
                sets=[CompletedSet(set_number=1, weight_kg=55.0, reps_performed=8)]
            )
        ]
    )

    metrics = ProgressAnalyzer.analyze_user_progress(sample_profile, [s1, s2])
    assert metrics.total_completed_sessions == 2
    assert metrics.total_volume_kg == (50.0 * 8) + (55.0 * 8)
    bench_record = metrics.exercise_records.get("ex_barbell_bench_press")
    assert bench_record is not None
    assert bench_record.trend == "increasing"
    assert len(metrics.recommended_adjustments) > 0
