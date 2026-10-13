"""Shared pytest fixtures for AI Workout Coach tests."""

import pytest
import tempfile
import os
from workout_coach.core.db import init_db
from workout_coach.core.repository import WorkoutRepository
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel
)
from workout_coach.agent.tools import WorkoutCoachTools
from workout_coach.agent.coach import WorkoutCoach
from workout_coach.agent.model_adapter import MockWorkoutCoachModelAdapter


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database file for test isolation."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def repo(temp_db):
    """Instantiate a repository bound to the isolated temporary test database."""
    return WorkoutRepository(temp_db)


@pytest.fixture
def tools(repo):
    """Instantiate tools with isolated test repository."""
    return WorkoutCoachTools(repo)


@pytest.fixture
def coach(repo):
    """Instantiate coach with isolated test repository and mock adapter."""
    return WorkoutCoach(repo=repo, model_adapter=MockWorkoutCoachModelAdapter())


@pytest.fixture
def sample_profile():
    """Standard healthy sample profile."""
    return FitnessProfile(
        user_id="test_user_01",
        fitness_goal=FitnessGoal.STRENGTH,
        experience_level=ExperienceLevel.INTERMEDIATE,
        available_equipment=["barbell", "dumbbells", "bench", "bodyweight"],
        days_per_week=3,
        session_duration_minutes=60,
        preferences=["compound_lifts"],
        limitations=[]
    )


@pytest.fixture
def injured_profile():
    """Sample profile with declared lower back and shoulder limitations."""
    return FitnessProfile(
        user_id="test_user_injured",
        fitness_goal=FitnessGoal.MUSCLE_GAIN,
        experience_level=ExperienceLevel.BEGINNER,
        available_equipment=["dumbbells", "bodyweight", "bench"],
        days_per_week=3,
        session_duration_minutes=45,
        preferences=["hypertrophy"],
        limitations=["lower_back_pain", "shoulder_impingement"]
    )
