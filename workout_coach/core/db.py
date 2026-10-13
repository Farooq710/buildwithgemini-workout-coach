"""Database connection and initialization module for AI Workout Coach."""

import sqlite3
import json
import os
from typing import Optional
from workout_coach.core.exercise_library import EXERCISE_CATALOG

DEFAULT_DB_PATH = os.environ.get("WORKOUT_COACH_DB_PATH", "/config/Desktop/BuildWithGemini/workout_coach.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and configure a SQLite connection with row factories and foreign keys enabled."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and seed exercise reference data."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fitness_profiles (
            user_id TEXT PRIMARY KEY,
            fitness_goal TEXT NOT NULL,
            experience_level TEXT NOT NULL,
            available_equipment TEXT NOT NULL,
            days_per_week INTEGER NOT NULL,
            session_duration_minutes INTEGER NOT NULL,
            preferences TEXT,
            limitations TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS exercises (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            movement_pattern TEXT NOT NULL,
            primary_muscles TEXT NOT NULL,
            secondary_muscles TEXT,
            equipment_required TEXT NOT NULL,
            instructions TEXT NOT NULL,
            substitutions TEXT,
            contraindications TEXT
        );

        CREATE TABLE IF NOT EXISTS workout_plans (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            goal TEXT NOT NULL,
            split_type TEXT NOT NULL,
            days_per_week INTEGER NOT NULL,
            rationale TEXT NOT NULL,
            sessions_json TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS completed_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            plan_id TEXT,
            session_date TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            perceived_effort_rpe INTEGER,
            exercises_json TEXT NOT NULL,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS completed_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            weight_kg REAL NOT NULL,
            reps_performed INTEGER NOT NULL,
            rpe INTEGER,
            is_completed INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES completed_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY(exercise_id) REFERENCES exercises(id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)

        # Seed exercises
        for ex in EXERCISE_CATALOG:
            conn.execute("""
            INSERT OR REPLACE INTO exercises (
                id, name, category, movement_pattern, primary_muscles, secondary_muscles,
                equipment_required, instructions, substitutions, contraindications
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ex.id,
                ex.name,
                ex.category.value,
                ex.movement_pattern.value,
                json.dumps(ex.primary_muscles),
                json.dumps(ex.secondary_muscles),
                json.dumps(ex.equipment_required),
                ex.instructions,
                json.dumps(ex.substitutions),
                json.dumps(ex.contraindications)
            ))
    conn.close()


def reset_db(db_path: Optional[str] = None) -> None:
    """Drop and recreate the database for clean testing."""
    path = db_path or DEFAULT_DB_PATH
    if os.path.exists(path):
        os.remove(path)
    init_db(path)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DEFAULT_DB_PATH)
