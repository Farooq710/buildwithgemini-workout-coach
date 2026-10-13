"""Deterministic fitness analytics and progression engine."""

from typing import List, Dict, Optional, Tuple
from datetime import date, timedelta
from workout_coach.core.models import (
    CompletedSession,
    FitnessProfile,
    ProgressMetrics,
    ExerciseProgressRecord
)
from workout_coach.core.exercise_library import get_exercise_by_id


def calculate_epley_1rm(weight_kg: float, reps: int) -> float:
    """Calculate Estimated 1-Repetition Maximum using the Epley equation."""
    if weight_kg <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return round(weight_kg, 1)
    # Epley formula is most valid for reps <= 12
    effective_reps = min(reps, 12)
    e1rm = weight_kg * (1.0 + (effective_reps / 30.0))
    return round(e1rm, 1)


def calculate_session_volume(session: CompletedSession) -> float:
    """Compute total volume load (kg * reps) for all completed sets in a session."""
    total_vol = 0.0
    for ex in session.exercises:
        if ex.skipped:
            continue
        for s in ex.sets:
            if s.is_completed and s.weight_kg > 0 and s.reps_performed > 0:
                total_vol += s.weight_kg * s.reps_performed
    return round(total_vol, 1)


class ProgressAnalyzer:
    """Deterministic calculation of workout trends, consistency, and overload adjustments."""

    @staticmethod
    def analyze_user_progress(
        profile: FitnessProfile,
        sessions: List[CompletedSession],
        window_days: int = 28
    ) -> ProgressMetrics:
        """Analyze user workout history over a trailing window."""
        if not sessions:
            return ProgressMetrics(
                user_id=profile.user_id,
                total_completed_sessions=0,
                weekly_adherence_rate=0.0,
                total_volume_kg=0.0,
                exercise_records={},
                recommended_adjustments=["No workout history found. Start your first session to track progress!"]
            )

        # 1. Total volume and session count
        total_volume = sum(calculate_session_volume(s) for s in sessions)
        total_sessions = len(sessions)

        # 2. Adherence rate over last 14 days
        cutoff_date = date.today() - timedelta(days=14)
        recent_sessions = [s for s in sessions if s.session_date >= cutoff_date]
        target_biweekly = profile.days_per_week * 2
        adherence_rate = round(len(recent_sessions) / max(1, target_biweekly), 2)

        # 3. Aggregate exercise-level performance
        exercise_logs: Dict[str, List[Tuple[date, float, int, float]]] = {}  # id -> list of (date, weight, reps, e1rm)
        for s in sorted(sessions, key=lambda x: x.session_date):
            for ex in s.exercises:
                if ex.skipped:
                    continue
                if ex.exercise_id not in exercise_logs:
                    exercise_logs[ex.exercise_id] = []
                for st in ex.sets:
                    if st.is_completed and st.reps_performed > 0:
                        e1rm = calculate_epley_1rm(st.weight_kg, st.reps_performed)
                        exercise_logs[ex.exercise_id].append(
                            (s.session_date, st.weight_kg, st.reps_performed, e1rm)
                        )

        exercise_records: Dict[str, ExerciseProgressRecord] = {}
        for ex_id, logs in exercise_logs.items():
            if not logs:
                continue
            ex_def = get_exercise_by_id(ex_id)
            name = ex_def.name if ex_def else ex_id
            weights = [l[1] for l in logs]
            e1rms = [l[3] for l in logs]
            total_ex_vol = sum(l[1] * l[2] for l in logs)

            # Trend calculation
            if len(logs) < 2:
                trend = "new"
            else:
                first_e1rm = max(l[3] for l in logs[:len(logs)//2])
                second_e1rm = max(l[3] for l in logs[len(logs)//2:])
                if second_e1rm > first_e1rm * 1.03:
                    trend = "increasing"
                elif second_e1rm < first_e1rm * 0.97:
                    trend = "decreasing"
                else:
                    trend = "stable"

            exercise_records[ex_id] = ExerciseProgressRecord(
                exercise_id=ex_id,
                exercise_name=name,
                sessions_logged=len(set(l[0] for l in logs)),
                latest_weight_kg=weights[-1],
                max_weight_kg=max(weights),
                estimated_1rm_kg=max(e1rms),
                total_volume_kg=round(total_ex_vol, 1),
                trend=trend
            )

        # 4. Generate deterministic adjustment recommendations
        recommendations = ProgressAnalyzer._generate_adjustments(profile, sessions, exercise_records)

        return ProgressMetrics(
            user_id=profile.user_id,
            total_completed_sessions=total_sessions,
            weekly_adherence_rate=adherence_rate,
            total_volume_kg=round(total_volume, 1),
            exercise_records=exercise_records,
            recommended_adjustments=recommendations
        )

    @staticmethod
    def _generate_adjustments(
        profile: FitnessProfile,
        sessions: List[CompletedSession],
        records: Dict[str, ExerciseProgressRecord]
    ) -> List[str]:
        """Derive actionable, rule-based training adjustments based on telemetry."""
        recs: List[str] = []

        if not sessions:
            return ["Complete your first workout to receive personalized progression adjustments."]

        latest_session = sessions[0]

        # Check latest session exertion rating
        if latest_session.perceived_effort_rpe is not None:
            if latest_session.perceived_effort_rpe <= 6:
                recs.append("Recent workout intensity was light (RPE ≤ 6). Consider adding 2.5kg or 1-2 reps on primary lifts.")
            elif latest_session.perceived_effort_rpe >= 9:
                recs.append("High strain recorded (RPE ≥ 9). Maintain current weights or increase rest periods by 30 seconds.")

        # Check qualitative feedback for soreness / fatigue
        if latest_session.feedback:
            fb = latest_session.feedback.lower()
            if any(w in fb for w in ["sore", "pain", "tight", "exhausted", "fatigued"]):
                recs.append("Fatigue or soreness reported in last session. Ensure at least 48 hours before training the same muscle group.")

        # Check progressive overload across specific movements
        overloaded = False
        for ex_id, rec in records.items():
            if rec.trend == "increasing" and rec.sessions_logged >= 2:
                recs.append(f"Strong progression on {rec.exercise_name}: Estimated 1RM reached {rec.estimated_1rm_kg}kg.")
                overloaded = True
                break
        
        if not overloaded and len(sessions) >= 3:
            recs.append("Weights have remained steady. On your next session, aim for 1 additional repetition on your top set before increasing weight.")

        return recs[:4]
