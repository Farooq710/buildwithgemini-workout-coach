FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    STORAGE_BACKEND=firestore

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY workout_coach /app/workout_coach
COPY main.py /app/main.py

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn workout_coach.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
