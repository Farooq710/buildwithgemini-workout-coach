"""Tests for curated exercise library and substitution searches."""

import pytest
from workout_coach.core.exercise_library import (
    search_exercises,
    get_exercise_by_id,
    find_safe_substitute
)
from workout_coach.core.models import ExerciseCategory, MovementPattern


def test_catalog_retrieval():
    """Verify core catalog exercises can be retrieved by ID."""
    bench = get_exercise_by_id("ex_barbell_bench_press")
    assert bench is not None
    assert bench.name == "Barbell Bench Press"
    assert "chest" in bench.primary_muscles
    assert "shoulder_impingement" in bench.contraindications


def test_equipment_filtering():
    """Verify searching with only bodyweight excludes barbell and cable exercises."""
    results = search_exercises(available_equipment=["bodyweight"])
    for ex in results:
        assert set(ex.equipment_required).issubset({"bodyweight"})


def test_contraindication_exclusion():
    """Verify searching while avoiding lower back pain filters out Deadlift and Bent-over Rows."""
    results = search_exercises(avoid_contraindications=["lower_back_pain"])
    ex_ids = [e.id for e in results]
    assert "ex_barbell_deadlift" not in ex_ids
    assert "ex_barbell_bent_over_row" not in ex_ids


def test_safe_substitutions():
    """Verify safe substitute can be found when primary exercise is contraindicated."""
    # When user has shoulder impingement, barbell bench press or OHP should substitute
    sub = find_safe_substitute(
        "ex_barbell_bench_press",
        avoid_contraindications=["shoulder_impingement"],
        available_equipment=["dumbbells", "bench"]
    )
    assert sub is not None
    assert "shoulder_impingement" not in sub.contraindications
