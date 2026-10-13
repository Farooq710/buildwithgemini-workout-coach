"""Domain models and schemas for AI Workout Coach."""

from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid
from pydantic import BaseModel, Field, ConfigDict, model_validator


class FitnessGoal(str, Enum):
    STRENGTH = "strength"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"
    ENDURANCE = "endurance"
    WEIGHT_MANAGEMENT = "weight_management"


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseCategory(str, Enum):
    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    CORE = "core"
    FULL_BODY = "full_body"


class MovementPattern(str, Enum):
    SQUAT = "squat"
    HINGE = "hinge"
    PRESS = "press"
    ROW = "row"
    PULLUP = "pullup"
    LUNGE = "lunge"
    CARRY = "carry"
    ISOLATION = "isolation"
    CORE = "core"


class FitnessProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: str
    fitness_goal: FitnessGoal
    experience_level: ExperienceLevel
    available_equipment: List[str] = Field(default_factory=lambda: ["bodyweight"])
    days_per_week: int = Field(default=3, ge=1, le=7)
    session_duration_minutes: int = Field(default=45, ge=15, le=180)
    preferences: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(
        default_factory=list,
        description="Declared injuries or restrictions: lower_back_pain, knee_pain, shoulder_impingement, wrist_pain, etc."
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Exercise(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    category: ExerciseCategory
    movement_pattern: MovementPattern
    primary_muscles: List[str]
    secondary_muscles: List[str] = Field(default_factory=list)
    equipment_required: List[str] = Field(default_factory=lambda: ["bodyweight"])
    instructions: str
    substitutions: List[str] = Field(default_factory=list)
    contraindications: List[str] = Field(
        default_factory=list,
        description="Conditions where this movement should be avoided (e.g. lower_back_pain, knee_pain)"
    )


class PlannedExercise(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exercise_id: str
    exercise_name: str
    order_in_session: int
    target_sets: int = Field(ge=1, le=10)
    target_reps: str = Field(description="e.g. '8-10' or '5' or '30s'")
    rest_seconds: int = Field(default=90, ge=15, le=300)
    notes: Optional[str] = None


class PlannedSession(BaseModel):
    model_config = ConfigDict(extra="ignore")

    day_number: int
    day_name: str
    focus: str
    exercises: List[PlannedExercise]
    warm_up: List[str] = Field(default_factory=list)
    cooldown: List[str] = Field(default_factory=list)


class WorkoutPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    plan_name: str
    goal: FitnessGoal
    split_type: str = Field(description="e.g. full_body, upper_lower, push_pull_legs")
    days_per_week: int
    sessions: List[PlannedSession]
    rationale: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CompletedSet(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    set_number: int
    weight_kg: float = Field(default=0.0, ge=0.0)
    reps_performed: int = Field(default=0, ge=0, alias="reps")
    rpe: Optional[float] = Field(default=None, ge=1.0, le=10.0, description="Rate of Perceived Exertion (1-10)")
    is_completed: bool = Field(default=True, alias="completed")

    @model_validator(mode="before")
    @classmethod
    def reconcile_set_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "reps" in data and "reps_performed" not in data:
                data["reps_performed"] = data["reps"]
            elif "reps_performed" in data and "reps" not in data:
                data["reps"] = data["reps_performed"]
            if "completed" in data and "is_completed" not in data:
                data["is_completed"] = data["completed"]
            elif "is_completed" in data and "completed" not in data:
                data["completed"] = data["is_completed"]
        return data


class CompletedExercise(BaseModel):
    model_config = ConfigDict(extra="ignore")

    exercise_id: str
    exercise_name: str
    sets: List[CompletedSet] = Field(default_factory=list)
    skipped: bool = False
    notes: Optional[str] = None


class CompletedSession(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:10]}")
    user_id: str
    plan_id: Optional[str] = None
    session_date: date = Field(default_factory=date.today)
    session_name: Optional[str] = "Completed Workout"
    duration_minutes: int = Field(default=45, ge=1, le=300)
    perceived_effort_rpe: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    exercises: List[CompletedExercise] = Field(default_factory=list)
    feedback: Optional[str] = None
    total_volume_kg: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="before")
    @classmethod
    def reconcile_session_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_date = data.get("session_date") or data.get("started_at")
            if raw_date:
                if isinstance(raw_date, str) and "T" in raw_date:
                    clean_d = raw_date.split("T")[0]
                elif isinstance(raw_date, datetime):
                    clean_d = raw_date.date()
                else:
                    clean_d = raw_date
                data["session_date"] = clean_d
                data["started_at"] = clean_d
            if "rpe_session" in data and "perceived_effort_rpe" not in data:
                data["perceived_effort_rpe"] = data["rpe_session"]
            if "feedback_notes" in data and "feedback" not in data:
                data["feedback"] = data["feedback_notes"]
            if not data.get("id"):
                data["id"] = f"sess_{uuid.uuid4().hex[:10]}"
        return data

    @model_validator(mode="after")
    def compute_volume_if_needed(self) -> "CompletedSession":
        if not self.total_volume_kg:
            vol = sum(
                (s.weight_kg * s.reps_performed)
                for ex in self.exercises
                for s in ex.sets
                if s.is_completed
            )
            self.total_volume_kg = round(vol, 2)
        return self


class ExerciseProgressRecord(BaseModel):
    exercise_id: str
    exercise_name: str
    sessions_logged: int
    latest_weight_kg: float
    max_weight_kg: float
    estimated_1rm_kg: float
    total_volume_kg: float
    trend: str = Field(description="increasing, stable, decreasing, new")


class ProgressMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    user_id: str
    total_completed_sessions: int
    total_sessions_completed: Optional[int] = None
    weekly_adherence_rate: float = Field(description="0.0 to 1.0 (or >1.0 if exceeding)")
    adherence_rate_14d: Optional[float] = None
    total_volume_kg: float
    exercise_records: Dict[str, ExerciseProgressRecord] = Field(default_factory=dict)
    exercise_trends: Optional[Dict[str, ExerciseProgressRecord]] = None
    recommended_adjustments: List[str] = Field(default_factory=list)
    progression_recommendations: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode="after")
    def sync_aliases(self) -> "ProgressMetrics":
        if self.total_sessions_completed is None:
            self.total_sessions_completed = self.total_completed_sessions
        if self.adherence_rate_14d is None:
            self.adherence_rate_14d = round(self.weekly_adherence_rate * 100, 1)
        if self.exercise_trends is None:
            self.exercise_trends = self.exercise_records
        if self.progression_recommendations is None:
            self.progression_recommendations = [
                {"exercise_name": "General", "recommendation": rec, "rationale": "Telemetry-driven"}
                for rec in self.recommended_adjustments
            ]
        return self


class ChatTurnRequest(BaseModel):
    user_id: str
    message: str


class ChatTurnResponse(BaseModel):
    reply: str
    intent: str
    executed_tools: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    safety_warning: Optional[str] = None
    a2ui_messages: Optional[List[Dict[str, Any]]] = Field(default=None, description="A2UI v0.8 messages payload")
    maps_data: Optional[Dict[str, Any]] = Field(default=None, description="Google Maps facilities data")
