"""FastAPI REST API server for AI Workout Coach with Cloud Firestore and SQLite persistence."""

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import logging

from workout_coach.core.models import (
    FitnessProfile,
    WorkoutPlan,
    CompletedSession,
    ProgressMetrics,
    ChatTurnRequest,
    ChatTurnResponse,
    ExerciseCategory,
    MovementPattern
)
from workout_coach.core.repository_factory import get_repository
from workout_coach.core.exercise_library import (
    search_exercises as search_ex,
    get_exercise_by_id,
    EXERCISE_CATALOG
)
from workout_coach.core.workout_planner import WorkoutPlanner
from workout_coach.core.progress_analyzer import ProgressAnalyzer
from workout_coach.agent.coach import WorkoutCoach
from workout_coach.agent.model_adapter import (
    MockWorkoutCoachModelAdapter,
    GeminiVertexModelAdapter
)

# App Configuration
app = FastAPI(
    title="AI Workout Coach API",
    description="Agent-First AI Workout Coach with Cloud Firestore, deterministic fitness intelligence, and safety guardrails.",
    version="1.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("workout_coach.api.main")

# Initialize Storage & Repository (Cloud Firestore default, SQLite fallback)
repo = get_repository()

# Determine model adapter
use_gemini = os.environ.get("USE_VERTEX_GEMINI", "false").lower() in ["true", "1", "yes"]
if use_gemini:
    adapter = GeminiVertexModelAdapter()
    logger.info("⚡ Active model adapter: GeminiVertexModelAdapter (Vertex AI Gemini 2.5 Flash)")
else:
    adapter = MockWorkoutCoachModelAdapter()
    logger.info("ℹ️ Active model adapter: MockWorkoutCoachModelAdapter (Deterministic/Offline)")

coach = WorkoutCoach(repo=repo, model_adapter=adapter)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")


# --- ROOT & HEALTH CHECK ---

@app.get("/")
def serve_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Workout Coach API active"}


@app.get("/api/v1/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "app": "AI Workout Coach",
        "storage_backend": repo.__class__.__name__,
        "model_adapter": adapter.__class__.__name__,
        "exercise_catalog_count": len(EXERCISE_CATALOG)
    }


# --- PROFILES ---

@app.post("/api/v1/profiles", response_model=FitnessProfile, status_code=status.HTTP_201_CREATED)
def create_or_update_profile(profile: FitnessProfile) -> FitnessProfile:
    return repo.save_profile(profile)


@app.get("/api/v1/profiles", response_model=List[FitnessProfile])
def list_profiles(include_internal: bool = True) -> List[FitnessProfile]:
    if hasattr(repo, "list_profiles"):
        all_profs = repo.list_profiles()
        if not include_internal:
            return [
                p for p in all_profs 
                if not (p.user_id.lower().startswith("test_") or p.user_id.lower().startswith("api_test_") or p.user_id.lower().startswith("tmp_") or p.user_id.lower().startswith("cloud_user_"))
            ]
        return all_profs
    return []


@app.get("/api/v1/profiles/{user_id}", response_model=FitnessProfile)
def get_profile(user_id: str) -> FitnessProfile:
    prof = repo.get_profile(user_id)
    if not prof:
        raise HTTPException(status_code=404, detail=f"Profile for user '{user_id}' not found.")
    return prof


# --- EXERCISE CATALOG ---

@app.get("/api/v1/exercises")
def list_exercises(
    query: Optional[str] = None,
    category: Optional[ExerciseCategory] = None,
    movement_pattern: Optional[MovementPattern] = None,
    equipment: Optional[str] = Query(None, description="Comma-separated equipment"),
    avoid: Optional[str] = Query(None, description="Comma-separated limitations to avoid")
) -> Dict[str, Any]:
    equip_list = [e.strip() for e in equipment.split(",")] if equipment else None
    avoid_list = [a.strip() for a in avoid.split(",")] if avoid else None
    results = search_ex(
        query=query,
        category=category,
        movement_pattern=movement_pattern,
        available_equipment=equip_list,
        avoid_contraindications=avoid_list,
        limit=50
    )
    return {
        "count": len(results),
        "exercises": [ex.model_dump() for ex in results]
    }


@app.get("/api/v1/exercises/{exercise_id}")
def get_exercise_detail(exercise_id: str) -> Dict[str, Any]:
    ex = get_exercise_by_id(exercise_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ex.model_dump()


# --- WORKOUT PLANS ---

class PlanGenerateRequest(BaseModel):
    user_id: Optional[str] = None
    plan_name: Optional[str] = None


@app.post("/api/v1/workout-plans", response_model=WorkoutPlan, status_code=status.HTTP_201_CREATED)
def generate_workout_plan(
    req: Optional[PlanGenerateRequest] = None,
    user_id: Optional[str] = Query(None)
) -> WorkoutPlan:
    actual_user_id = (req.user_id if req and req.user_id else None) or user_id
    if not actual_user_id:
        raise HTTPException(status_code=400, detail="user_id is required either in request body or query parameter.")
    p_name = req.plan_name if req else None
    profile = repo.get_profile(actual_user_id)
    if not profile:
        raise HTTPException(status_code=400, detail=f"Cannot generate plan: User profile '{actual_user_id}' does not exist.")
    plan = WorkoutPlanner.generate_plan(profile, plan_name=p_name)
    return repo.save_workout_plan(plan)


@app.get("/api/v1/workout-plans/{user_id}/current", response_model=WorkoutPlan)
def get_current_plan(user_id: str) -> WorkoutPlan:
    plan = repo.get_current_workout_plan(user_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No active workout plan found for user.")
    return plan


# --- SESSIONS & LOGGING ---

@app.post("/api/v1/workout-sessions", response_model=CompletedSession, status_code=status.HTTP_201_CREATED)
def log_session(session: CompletedSession) -> CompletedSession:
    return repo.save_completed_session(session)


@app.get("/api/v1/workout-history/{user_id}", response_model=List[CompletedSession])
def get_workout_history(user_id: str, limit: int = 20) -> List[CompletedSession]:
    return repo.get_completed_sessions(user_id, limit=limit)


# --- PROGRESS ANALYTICS ---

@app.get("/api/v1/progress/{user_id}", response_model=ProgressMetrics)
def get_progress_metrics(user_id: str) -> ProgressMetrics:
    profile = repo.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    sessions = repo.get_completed_sessions(user_id, limit=50)
    return ProgressAnalyzer.analyze_user_progress(profile, sessions)


# --- CONVERSATIONAL COACH CHAT ---

@app.post("/api/v1/coach/chat", response_model=ChatTurnResponse)
def chat_with_coach(req: ChatTurnRequest) -> ChatTurnResponse:
    return coach.process_message(user_id=req.user_id, message=req.message)


# --- GOOGLE MAPS & PLACES SCOUT ---

@app.get("/api/v1/maps/facilities")
def get_nearby_facilities(
    location: str = Query(..., description="Location, city or address"),
    facility_type: str = Query("gym", description="Type of facility: gym, running track, calisthenics park, powerlifting")
) -> Dict[str, Any]:
    """Scout nearby fitness facilities using Google Maps and Places (New) API with fallback."""
    from workout_coach.core.maps_service import GoogleMapsService
    maps_svc = GoogleMapsService()
    return maps_svc.search_fitness_facilities(location=location, facility_type=facility_type)


# Mount static assets
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
