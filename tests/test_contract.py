"""Contract tests validating the frontend telemetry contract, payload shape,
volume computation, and progress KPI guarantees.
"""

import pytest
from fastapi.testclient import TestClient
from workout_coach.api.main import app

client = TestClient(app)


def test_frontend_session_logging_contract():
    """Verify that the frontend's exact submitted JSON payload matches the backend contract,
    returns HTTP 201, computes non-zero volume, and updates progress telemetry.
    """
    user_id = "contract_athlete_01"

    # 1. Seed athlete profile
    profile_payload = {
        "user_id": user_id,
        "fitness_goal": "strength",
        "experience_level": "intermediate",
        "available_equipment": ["barbell", "dumbbells", "bench"],
        "days_per_week": 3,
        "session_duration_minutes": 60,
        "preferences": ["powerlifting"],
        "limitations": []
    }
    client.post("/api/v1/profiles", json=profile_payload)

    # 2. Frontend submission payload shape (exact schema emitted by static/app.js)
    frontend_payload = {
        "id": "sess_contract_test_101",
        "user_id": user_id,
        "session_name": "Completed Workout",
        "session_date": "2026-10-13",
        "started_at": "2026-10-13T10:00:00.000Z",
        "duration_minutes": 55,
        "perceived_effort_rpe": 8.5,
        "rpe_session": 8.5,
        "feedback": "Felt great on bench press today",
        "feedback_notes": "Felt great on bench press today",
        "exercises": [
            {
                "exercise_id": "barbell_bench_press",
                "exercise_name": "Barbell Bench Press",
                "sets": [
                    {
                        "set_number": 1,
                        "weight_kg": 60.0,
                        "reps": 10,
                        "reps_performed": 10,
                        "rpe": 7.0,
                        "completed": True,
                        "is_completed": True
                    },
                    {
                        "set_number": 2,
                        "weight_kg": 70.0,
                        "reps": 8,
                        "reps_performed": 8,
                        "rpe": 8.0,
                        "completed": True,
                        "is_completed": True
                    },
                    {
                        "set_number": 3,
                        "weight_kg": 80.0,
                        "reps": 6,
                        "reps_performed": 6,
                        "rpe": 8.5,
                        "completed": True,
                        "is_completed": True
                    }
                ],
                "skipped": False
            }
        ]
    }

    # Submit workout session
    res = client.post("/api/v1/workout-sessions", json=frontend_payload)
    assert res.status_code == 201, f"Failed contract test: {res.text}"
    session_data = res.json()

    # Validate returned contract
    assert session_data["id"] == "sess_contract_test_101"
    assert session_data["user_id"] == user_id
    assert session_data["session_date"] == "2026-10-13"
    # Volume: 60*10 + 70*8 + 80*6 = 600 + 560 + 480 = 1640 kg
    assert session_data["total_volume_kg"] == 1640.0

    # 3. Verify Progress Endpoint guarantees
    prog_res = client.get(f"/api/v1/progress/{user_id}")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()

    # Dual contract verification for frontend compatibility
    assert prog_data.get("total_sessions_completed", 0) >= 1
    assert prog_data.get("total_completed_sessions", 0) >= 1
    assert prog_data.get("total_volume_kg", 0.0) >= 1640.0

    # Adherence rates
    assert "adherence_rate_14d" in prog_data
    assert "weekly_adherence_rate" in prog_data

    # Trend / record telemetry
    trends = prog_data.get("exercise_records") or prog_data.get("exercise_trends") or {}
    assert "Barbell Bench Press" in trends or "barbell_bench_press" in trends
    key = "Barbell Bench Press" if "Barbell Bench Press" in trends else "barbell_bench_press"
    bench_stat = trends[key]
    assert bench_stat["max_weight_kg"] >= 80.0
    assert bench_stat["estimated_1rm_kg"] > 80.0
    assert bench_stat["total_volume_kg"] >= 1640.0


def test_legacy_payload_contract_tolerance():
    """Verify backend tolerates legacy or missing fields (omitted id, started_at string,
    float RPE) without returning 422 or dropping volume computation.
    """
    user_id = "contract_athlete_legacy"

    legacy_payload = {
        "user_id": user_id,
        "started_at": "2026-10-12T15:30:00Z",
        "duration_minutes": 40,
        "rpe_session": 8.5,
        "feedback_notes": "Quick dumbbell session",
        "exercises": [
            {
                "exercise_id": "dumbbell_goblet_squat",
                "exercise_name": "Goblet Squat",
                "sets": [
                    {
                        "set_number": 1,
                        "weight_kg": 24.0,
                        "reps": 12,
                        "rpe": 8.0,
                        "completed": True
                    }
                ]
            }
        ]
    }

    res = client.post("/api/v1/workout-sessions", json=legacy_payload)
    assert res.status_code == 201, f"Legacy payload failed: {res.text}"
    data = res.json()
    assert data["id"].startswith("sess_")
    assert data["total_volume_kg"] == 24.0 * 12  # 288.0 kg
