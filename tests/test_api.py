"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from workout_coach.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify /api/v1/health returns 200 and healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["exercise_catalog_count"] >= 30


def test_profile_api_lifecycle():
    """Verify creating and retrieving profile via API."""
    user_id = "api_test_user_01"
    payload = {
        "user_id": user_id,
        "fitness_goal": "muscle_gain",
        "experience_level": "intermediate",
        "available_equipment": ["dumbbells", "bench", "bodyweight"],
        "days_per_week": 4,
        "session_duration_minutes": 50,
        "preferences": ["hypertrophy"],
        "limitations": []
    }

    # Create profile
    res = client.post("/api/v1/profiles", json=payload)
    assert res.status_code == 201
    assert res.json()["user_id"] == user_id

    # Retrieve profile
    get_res = client.get(f"/api/v1/profiles/{user_id}")
    assert get_res.status_code == 200
    assert get_res.json()["days_per_week"] == 4

    # List profiles
    list_res = client.get("/api/v1/profiles")
    assert list_res.status_code == 200
    profiles = list_res.json()
    assert isinstance(profiles, list)
    assert any(p["user_id"] == user_id for p in profiles)


def test_exercise_search_api():
    """Verify exercise query API endpoint."""
    res = client.get("/api/v1/exercises?query=bench")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0


def test_chat_api():
    """Verify coach chat endpoint."""
    payload = {
        "user_id": "api_chat_user",
        "message": "Hello coach, what exercises do you have for back?"
    }
    res = client.post("/api/v1/coach/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
