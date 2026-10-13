"""The 9 Core Agent Tool Definitions with strict typing, validation, and persistence."""

from typing import Dict, Any, List, Optional
import uuid
from datetime import date
import urllib.parse

from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel,
    ExerciseCategory,
    CompletedSession,
    CompletedExercise,
    CompletedSet
)
from workout_coach.core.repository import WorkoutRepository
from workout_coach.core.exercise_library import search_exercises as search_ex_lib
from workout_coach.core.workout_planner import WorkoutPlanner
from workout_coach.core.progress_analyzer import ProgressAnalyzer
from workout_coach.core.maps_service import GoogleMapsService


class WorkoutCoachTools:
    """Tool execution harness for the AI Workout Coach."""

    def __init__(self, repo: Optional[WorkoutRepository] = None, maps_service: Optional[GoogleMapsService] = None):
        self.repo = repo or WorkoutRepository()
        self.maps_service = maps_service or GoogleMapsService()

    # Tool 1: get_fitness_profile
    def get_fitness_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetch the user's active fitness profile."""
        profile = self.repo.get_profile(user_id)
        if not profile:
            return {
                "status": "not_found",
                "message": f"No fitness profile found for user '{user_id}'. Please create a profile first."
            }
        return {
            "status": "success",
            "profile": profile.model_dump()
        }

    # Tool 2: update_fitness_profile
    def update_fitness_profile(
        self,
        user_id: str,
        fitness_goal: Optional[str] = None,
        experience_level: Optional[str] = None,
        available_equipment: Optional[List[str]] = None,
        days_per_week: Optional[int] = None,
        session_duration_minutes: Optional[int] = None,
        preferences: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create or update user's fitness profile with validated fields."""
        existing = self.repo.get_profile(user_id)
        
        # Parse or default values
        goal_val = FitnessGoal(fitness_goal) if fitness_goal else (existing.fitness_goal if existing else FitnessGoal.GENERAL_FITNESS)
        exp_val = ExperienceLevel(experience_level) if experience_level else (existing.experience_level if existing else ExperienceLevel.BEGINNER)
        equip_val = available_equipment if available_equipment is not None else (existing.available_equipment if existing else ["bodyweight"])
        days_val = days_per_week if days_per_week is not None else (existing.days_per_week if existing else 3)
        duration_val = session_duration_minutes if session_duration_minutes is not None else (existing.session_duration_minutes if existing else 45)
        pref_val = preferences if preferences is not None else (existing.preferences if existing else [])
        lim_val = limitations if limitations is not None else (existing.limitations if existing else [])

        profile = FitnessProfile(
            user_id=user_id,
            fitness_goal=goal_val,
            experience_level=exp_val,
            available_equipment=equip_val,
            days_per_week=days_val,
            session_duration_minutes=duration_val,
            preferences=pref_val,
            limitations=lim_val
        )

        saved = self.repo.save_profile(profile)
        return {
            "status": "success",
            "message": "Fitness profile saved successfully.",
            "profile": saved.model_dump()
        }

    # Tool 3: create_workout_plan
    def create_workout_plan(self, user_id: str, plan_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate, validate, and store a personalized workout plan for the user."""
        profile = self.repo.get_profile(user_id)
        if not profile:
            return {
                "status": "error",
                "message": "Cannot generate plan: User profile does not exist. Please create a profile first."
            }

        plan = WorkoutPlanner.generate_plan(profile, plan_name=plan_name)
        saved_plan = self.repo.save_workout_plan(plan)

        return {
            "status": "success",
            "message": f"Generated new plan '{saved_plan.plan_name}' across {saved_plan.days_per_week} days.",
            "plan": saved_plan.model_dump()
        }

    # Tool 4: get_current_workout_plan
    def get_current_workout_plan(self, user_id: str) -> Dict[str, Any]:
        """Retrieve the user's currently active workout plan."""
        plan = self.repo.get_current_workout_plan(user_id)
        if not plan:
            return {
                "status": "not_found",
                "message": f"No active workout plan found for user '{user_id}'."
            }
        return {
            "status": "success",
            "plan": plan.model_dump()
        }

    # Tool 5: search_exercises
    def search_exercises(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        equipment: Optional[List[str]] = None,
        avoid_contraindications: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search the curated exercise library with safety filtering."""
        cat_enum = ExerciseCategory(category) if category else None
        results = search_ex_lib(
            query=query,
            category=cat_enum,
            available_equipment=equipment,
            avoid_contraindications=avoid_contraindications,
            limit=10
        )
        return {
            "status": "success",
            "count": len(results),
            "exercises": [ex.model_dump() for ex in results]
        }

    # Tool 6: log_workout_session
    def log_workout_session(self, user_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record completed workout session and store set-level telemetry."""
        plan = self.repo.get_current_workout_plan(user_id)
        
        # Parse exercises
        completed_exercises: List[CompletedExercise] = []
        for raw_ex in session_data.get("exercises", []):
            sets_list: List[CompletedSet] = []
            for s in raw_ex.get("sets", []):
                sets_list.append(CompletedSet(
                    set_number=s.get("set_number", 1),
                    weight_kg=float(s.get("weight_kg", 0.0)),
                    reps_performed=int(s.get("reps_performed", 0)),
                    rpe=s.get("rpe"),
                    is_completed=s.get("is_completed", True)
                ))
            completed_exercises.append(CompletedExercise(
                exercise_id=raw_ex.get("exercise_id"),
                exercise_name=raw_ex.get("exercise_name", raw_ex.get("exercise_id")),
                sets=sets_list,
                skipped=raw_ex.get("skipped", False),
                notes=raw_ex.get("notes")
            ))

        s_date = date.fromisoformat(session_data["session_date"]) if "session_date" in session_data else date.today()

        session = CompletedSession(
            id=session_data.get("id") or f"sess_{uuid.uuid4().hex[:10]}",
            user_id=user_id,
            plan_id=session_data.get("plan_id") or (plan.id if plan else None),
            session_date=s_date,
            duration_minutes=int(session_data.get("duration_minutes", 45)),
            perceived_effort_rpe=session_data.get("perceived_effort_rpe"),
            exercises=completed_exercises,
            feedback=session_data.get("feedback")
        )

        saved = self.repo.save_completed_session(session)
        return {
            "status": "success",
            "message": "Workout session logged and persisted successfully.",
            "session_id": saved.id,
            "exercises_logged": len(saved.exercises)
        }

    # Tool 7: get_workout_history
    def get_workout_history(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """Retrieve recent completed workouts."""
        sessions = self.repo.get_completed_sessions(user_id, limit=limit)
        return {
            "status": "success",
            "count": len(sessions),
            "sessions": [s.model_dump() for s in sessions]
        }

    # Tool 8: calculate_progress
    def calculate_progress(self, user_id: str) -> Dict[str, Any]:
        """Compute deterministic volume, adherence, and e1RM trends."""
        profile = self.repo.get_profile(user_id)
        if not profile:
            return {
                "status": "error",
                "message": "Cannot calculate progress: User profile not found."
            }
        sessions = self.repo.get_completed_sessions(user_id, limit=50)
        metrics = ProgressAnalyzer.analyze_user_progress(profile, sessions)
        return {
            "status": "success",
            "metrics": metrics.model_dump()
        }

    # Tool 9: suggest_workout_adjustment
    def suggest_workout_adjustment(self, user_id: str, session_feedback: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate recent performance and suggest progressive overload or deload adjustments."""
        profile = self.repo.get_profile(user_id)
        if not profile:
            return {
                "status": "error",
                "message": "User profile not found."
            }
        sessions = self.repo.get_completed_sessions(user_id, limit=10)
        metrics = ProgressAnalyzer.analyze_user_progress(profile, sessions)

        adjustments = list(metrics.recommended_adjustments)
        if session_feedback:
            fb = session_feedback.lower()
            if "too hard" in fb or "struggled" in fb:
                adjustments.insert(0, "User reported high difficulty: Drop next session's weight by 5% to consolidate technique.")
            elif "too easy" in fb:
                adjustments.insert(0, "User reported low difficulty: Add 2.5kg or 2 additional reps to target sets.")

        return {
            "status": "success",
            "user_id": user_id,
            "adherence_rate": metrics.weekly_adherence_rate,
            "total_volume_kg": metrics.total_volume_kg,
            "suggested_adjustments": adjustments
        }

    # Tool 10: find_nearby_gyms
    def find_nearby_gyms(
        self,
        location: str,
        facility_type: str = "gym",
        radius_meters: int = 5000,
        page_size: int = 4
    ) -> Dict[str, Any]:
        """Find nearby gyms, fitness centers, calisthenics parks, or running tracks using Google Maps API.
        
        Args:
            location: Address, city, neighborhood, or zip code (e.g. 'Austin, TX', 'Downtown Seattle', '78701')
            facility_type: Type of facility ('gym', 'crossfit', 'running track', 'calisthenics park', 'powerlifting')
            radius_meters: Search radius in meters (default: 5000)
            page_size: Max number of locations to retrieve
        """
        return self.maps_service.search_fitness_facilities(
            location=location,
            facility_type=facility_type,
            radius_meters=radius_meters,
            page_size=page_size
        )

    # Tool 11: get_location_coordinates
    def get_location_coordinates(self, address: str) -> Dict[str, Any]:
        """Get approximate latitude and longitude coordinates for an address or city."""
        encoded = urllib.parse.quote_plus(address)
        return {
            "status": "success",
            "address": address,
            "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={encoded}",
            "directions_url": f"https://www.google.com/maps/dir/?api=1&destination={encoded}"
        }
