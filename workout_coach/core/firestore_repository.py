"""Cloud Firestore persistent repository implementation for AI Workout Coach."""

import os
import logging
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from workout_coach.core.models import (
    FitnessProfile,
    WorkoutPlan,
    CompletedSession,
    CompletedExercise,
    CompletedSet
)
from workout_coach.core.exercise_library import EXERCISE_CATALOG

logger = logging.getLogger("workout_coach.core.firestore_repository")

# Hardcode GCP Project ID as required by Track 3 lab guidelines
DEFAULT_FIRESTORE_PROJECT = "qwiklabs-gcp-04-9ecf92a8e298"


class FirestoreWorkoutRepository:
    """Production-grade persistent repository backed by Google Cloud Firestore."""

    def __init__(self, project_id: Optional[str] = None, database: str = "(default)"):
        self.project_id = project_id or os.environ.get("FIRESTORE_PROJECT_ID", DEFAULT_FIRESTORE_PROJECT)
        self.database = database
        self.db = firestore.Client(project=self.project_id, database=self.database)
        
        # Collection references
        self.users_col = self.db.collection("users")
        self.plans_col = self.db.collection("workout_plans")
        self.sessions_col = self.db.collection("workout_sessions")
        self.chat_col = self.db.collection("chat_history")
        self.exercises_col = self.db.collection("exercises")

    def seed_exercises(self) -> int:
        """Seed the Firestore exercises collection from catalog if empty."""
        batch = self.db.batch()
        count = 0
        for ex in EXERCISE_CATALOG:
            doc_ref = self.exercises_col.document(ex.id)
            doc_data = ex.model_dump()
            batch.set(doc_ref, doc_data)
            count += 1
        batch.commit()
        logger.info("Successfully seeded %d exercises to Cloud Firestore.", count)
        return count

    # --- ATHLETE PROFILES ---

    def save_profile(self, profile: FitnessProfile) -> FitnessProfile:
        doc_ref = self.users_col.document(profile.user_id)
        data = profile.model_dump()
        now_iso = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = now_iso
        if not data.get("created_at"):
            data["created_at"] = now_iso
        doc_ref.set(data)
        return profile

    def get_profile(self, user_id: str) -> Optional[FitnessProfile]:
        doc = self.users_col.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return FitnessProfile.model_validate(data)

    def list_profiles(self) -> List[FitnessProfile]:
        """Retrieve all athlete profiles from Cloud Firestore."""
        docs = self.users_col.stream()
        profiles: List[FitnessProfile] = []
        for doc in docs:
            try:
                data = doc.to_dict()
                profiles.append(FitnessProfile.model_validate(data))
            except Exception as e:
                logger.warning("Error parsing profile document %s: %s", doc.id, e)
        profiles.sort(key=lambda p: str(p.updated_at or p.created_at or ""), reverse=True)
        return profiles

    # --- WORKOUT PLANS ---

    def save_workout_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        # Mark prior plans inactive for this user
        prior_plans = (
            self.plans_col
            .where(filter=FieldFilter("user_id", "==", plan.user_id))
            .where(filter=FieldFilter("is_active", "==", True))
            .stream()
        )
        batch = self.db.batch()
        for p in prior_plans:
            batch.update(p.reference, {"is_active": False})
        batch.commit()

        # Save new plan
        data = plan.model_dump()
        self.plans_col.document(plan.id).set(data)
        return plan

    def get_current_workout_plan(self, user_id: str) -> Optional[WorkoutPlan]:
        docs = (
            self.plans_col
            .where(filter=FieldFilter("user_id", "==", user_id))
            .where(filter=FieldFilter("is_active", "==", True))
            .limit(1)
            .stream()
        )
        for doc in docs:
            return WorkoutPlan.model_validate(doc.to_dict())
        return None

    # --- COMPLETED SESSIONS & LOGS ---

    def save_completed_session(self, session: CompletedSession) -> CompletedSession:
        data = session.model_dump()
        if isinstance(data.get("session_date"), (datetime, date)):
            data["session_date"] = str(data["session_date"])
        data["logged_at"] = datetime.now(timezone.utc).isoformat()
        self.sessions_col.document(session.id).set(data)
        return session

    def get_completed_sessions(self, user_id: str, limit: int = 20) -> List[CompletedSession]:
        docs = (
            self.sessions_col
            .where(filter=FieldFilter("user_id", "==", user_id))
            .limit(limit)
            .stream()
        )
        sessions: List[CompletedSession] = []
        for doc in docs:
            d = doc.to_dict()
            if isinstance(d.get("session_date"), str):
                d["session_date"] = date.fromisoformat(d["session_date"])
            sessions.append(CompletedSession.model_validate(d))
        
        # Sort newest first
        sessions.sort(key=lambda s: s.session_date, reverse=True)
        return sessions

    def get_exercise_sets_history(self, user_id: str, exercise_id: str) -> List[Dict[str, Any]]:
        sessions = self.get_completed_sessions(user_id, limit=50)
        history = []
        for s in sessions:
            for ex in s.exercises:
                if ex.exercise_id == exercise_id:
                    for st in ex.sets:
                        history.append({
                            "session_id": s.id,
                            "session_date": str(s.session_date),
                            "exercise_id": exercise_id,
                            "exercise_name": ex.exercise_name,
                            "set_number": st.set_number,
                            "weight_kg": st.weight_kg,
                            "reps_performed": st.reps_performed,
                            "rpe": st.rpe,
                            "is_completed": st.is_completed
                        })
        return history

    # --- CHAT AUDIT HISTORY ---

    def save_chat_message(
        self,
        user_id: str,
        role: str,
        content: str,
        tool_calls: Optional[str] = None
    ) -> None:
        doc_id = f"{user_id}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        self.chat_col.document(doc_id).set({
            "user_id": user_id,
            "role": role,
            "content": content,
            "tool_calls": tool_calls,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        docs = (
            self.chat_col
            .where(filter=FieldFilter("user_id", "==", user_id))
            .limit(limit)
            .stream()
        )
        msgs = [d.to_dict() for d in docs]
        msgs.sort(key=lambda m: m.get("created_at", ""))
        return msgs
