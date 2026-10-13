"""Transactional repository implementation for AI Workout Coach persistence."""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import sqlite3

from workout_coach.core.db import get_connection
from workout_coach.core.models import (
    FitnessProfile,
    FitnessGoal,
    ExperienceLevel,
    WorkoutPlan,
    PlannedSession,
    CompletedSession,
    CompletedExercise,
    CompletedSet
)


class WorkoutRepository:
    """Repository managing profiles, plans, session logs, and chat records."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    # --- USER & PROFILE ---

    def ensure_user(self, user_id: str, name: Optional[str] = None) -> None:
        """Create user record if it does not already exist."""
        conn = self._get_conn()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)",
                (user_id, name or f"Athlete-{user_id[:6]}")
            )
        conn.close()

    def save_profile(self, profile: FitnessProfile) -> FitnessProfile:
        """Persist or update a fitness profile."""
        self.ensure_user(profile.user_id)
        conn = self._get_conn()
        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO fitness_profiles (
                user_id, fitness_goal, experience_level, available_equipment,
                days_per_week, session_duration_minutes, preferences, limitations, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.fitness_goal.value,
                profile.experience_level.value,
                json.dumps(profile.available_equipment),
                profile.days_per_week,
                profile.session_duration_minutes,
                json.dumps(profile.preferences),
                json.dumps(profile.limitations),
                datetime.utcnow().isoformat()
            ))
        conn.close()
        return profile

    def get_profile(self, user_id: str) -> Optional[FitnessProfile]:
        """Retrieve a user's fitness profile."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM fitness_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None

        return FitnessProfile(
            user_id=row["user_id"],
            fitness_goal=FitnessGoal(row["fitness_goal"]),
            experience_level=ExperienceLevel(row["experience_level"]),
            available_equipment=json.loads(row["available_equipment"]),
            days_per_week=row["days_per_week"],
            session_duration_minutes=row["session_duration_minutes"],
            preferences=json.loads(row["preferences"] or "[]"),
            limitations=json.loads(row["limitations"] or "[]"),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow()
        )

    def list_profiles(self) -> List[FitnessProfile]:
        """Retrieve all athlete profiles."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM fitness_profiles ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        profiles = []
        for row in rows:
            profiles.append(FitnessProfile(
                user_id=row["user_id"],
                fitness_goal=FitnessGoal(row["fitness_goal"]),
                experience_level=ExperienceLevel(row["experience_level"]),
                available_equipment=json.loads(row["available_equipment"]),
                days_per_week=row["days_per_week"],
                session_duration_minutes=row["session_duration_minutes"],
                preferences=json.loads(row["preferences"] or "[]"),
                limitations=json.loads(row["limitations"] or "[]"),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.utcnow()
            ))
        return profiles

    # --- WORKOUT PLANS ---

    def save_workout_plan(self, plan: WorkoutPlan) -> WorkoutPlan:
        """Save a workout plan and set it as active."""
        self.ensure_user(plan.user_id)
        conn = self._get_conn()
        with conn:
            # Mark previous plans for this user as inactive
            conn.execute(
                "UPDATE workout_plans SET is_active = 0 WHERE user_id = ?",
                (plan.user_id,)
            )
            # Insert the new plan
            sessions_data = [s.model_dump() for s in plan.sessions]
            conn.execute("""
            INSERT OR REPLACE INTO workout_plans (
                id, user_id, plan_name, goal, split_type, days_per_week,
                rationale, sessions_json, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.id,
                plan.user_id,
                plan.plan_name,
                plan.goal.value,
                plan.split_type,
                plan.days_per_week,
                plan.rationale,
                json.dumps(sessions_data),
                1 if plan.is_active else 0,
                plan.created_at.isoformat()
            ))
        conn.close()
        return plan

    def get_current_workout_plan(self, user_id: str) -> Optional[WorkoutPlan]:
        """Fetch the currently active workout plan for a user."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM workout_plans WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None

        sessions_raw = json.loads(row["sessions_json"])
        sessions = [PlannedSession(**s) for s in sessions_raw]

        return WorkoutPlan(
            id=row["id"],
            user_id=row["user_id"],
            plan_name=row["plan_name"],
            goal=FitnessGoal(row["goal"]),
            split_type=row["split_type"],
            days_per_week=row["days_per_week"],
            rationale=row["rationale"],
            sessions=sessions,
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"])
        )

    # --- COMPLETED SESSIONS & SETS ---

    def save_completed_session(self, session: CompletedSession) -> CompletedSession:
        """Persist a completed workout session with set-level telemetry."""
        self.ensure_user(session.user_id)
        conn = self._get_conn()
        with conn:
            exercises_data = [ex.model_dump() for ex in session.exercises]
            conn.execute("""
            INSERT OR REPLACE INTO completed_sessions (
                id, user_id, plan_id, session_date, duration_minutes,
                perceived_effort_rpe, exercises_json, feedback, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.user_id,
                session.plan_id,
                session.session_date.isoformat(),
                session.duration_minutes,
                session.perceived_effort_rpe,
                json.dumps(exercises_data),
                session.feedback,
                session.created_at.isoformat()
            ))

            # Record individual sets into completed_sets for fast arithmetic indexing
            for ex in session.exercises:
                if ex.skipped:
                    continue
                for s in ex.sets:
                    conn.execute("""
                    INSERT INTO completed_sets (
                        session_id, user_id, exercise_id, set_number,
                        weight_kg, reps_performed, rpe, is_completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session.id,
                        session.user_id,
                        ex.exercise_id,
                        s.set_number,
                        s.weight_kg,
                        s.reps_performed,
                        s.rpe,
                        1 if s.is_completed else 0
                    ))
        conn.close()
        return session

    def get_completed_sessions(self, user_id: str, limit: int = 50) -> List[CompletedSession]:
        """Retrieve recent completed workout sessions in descending chronological order."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM completed_sessions WHERE user_id = ? ORDER BY session_date DESC, created_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()

        sessions: List[CompletedSession] = []
        for r in rows:
            ex_list = [CompletedExercise(**e) for e in json.loads(r["exercises_json"])]
            sessions.append(CompletedSession(
                id=r["id"],
                user_id=r["user_id"],
                plan_id=r["plan_id"],
                session_date=date.fromisoformat(r["session_date"]),
                duration_minutes=r["duration_minutes"],
                perceived_effort_rpe=r["perceived_effort_rpe"],
                exercises=ex_list,
                feedback=r["feedback"],
                created_at=datetime.fromisoformat(r["created_at"])
            ))
        return sessions

    def get_exercise_sets_history(self, user_id: str, exercise_id: str) -> List[Dict[str, Any]]:
        """Retrieve historical sets performed for a specific exercise."""
        conn = self._get_conn()
        cursor = conn.execute("""
        SELECT cs.session_id, cs.exercise_id, cs.set_number, cs.weight_kg, cs.reps_performed,
               cs.rpe, cs.is_completed, s.session_date
        FROM completed_sets cs
        JOIN completed_sessions s ON cs.session_id = s.id
        WHERE cs.user_id = ? AND cs.exercise_id = ?
        ORDER BY s.session_date ASC, cs.id ASC
        """, (user_id, exercise_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- CHAT HISTORY ---

    def save_chat_message(self, user_id: str, role: str, content: str, tool_calls: Optional[str] = None) -> None:
        """Store conversational message for context preservation."""
        self.ensure_user(user_id)
        conn = self._get_conn()
        with conn:
            conn.execute(
                "INSERT INTO chat_history (user_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
                (user_id, role, content, tool_calls)
            )
        conn.close()

    def get_chat_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent chat history."""
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT role, content, tool_calls, created_at FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in reversed(rows)]
