#!/usr/bin/env python3
"""AI Workout Coach Application Entry Point."""

import uvicorn
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 Starting AI Workout Coach server at http://{host}:{port}")
    uvicorn.run("workout_coach.api.main:app", host=host, port=port, reload=False)
