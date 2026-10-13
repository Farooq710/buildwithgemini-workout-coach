"""Repository factory to select between Cloud Firestore and SQLite based on environment."""

import os
import logging
from workout_coach.core.repository import WorkoutRepository
from workout_coach.core.db import DEFAULT_DB_PATH, init_db

logger = logging.getLogger("workout_coach.core.repository_factory")


def get_repository(backend: str = None):
    """Returns the active repository instance.
    
    Priority:
    1. 'backend' argument if provided.
    2. STORAGE_BACKEND environment variable ('firestore' or 'sqlite').
    3. Auto-fallback to SQLite if Firestore connection fails or offline.
    """
    selected = (backend or os.environ.get("STORAGE_BACKEND", "firestore")).lower()
    
    if selected == "firestore":
        try:
            from workout_coach.core.firestore_repository import FirestoreWorkoutRepository
            project_id = os.environ.get("FIRESTORE_PROJECT_ID", "qwiklabs-gcp-04-9ecf92a8e298")
            repo = FirestoreWorkoutRepository(project_id=project_id)
            logger.info("Initialized Cloud Firestore repository (Project: %s)", project_id)
            return repo
        except Exception as e:
            logger.warning("Cloud Firestore initialization failed: %s. Falling back to SQLite.", e)

    init_db(DEFAULT_DB_PATH)
    logger.info("Initialized local SQLite repository at %s", DEFAULT_DB_PATH)
    return WorkoutRepository(DEFAULT_DB_PATH)
