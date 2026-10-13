# Project Brief: AI Workout Coach

**Project Name:** AI Workout Coach (`ai-workout-coach`)  
**Status:** MVP Prototype Definition  
**Date:** 2026-10-13  
**Authors:** Senior AI Agent Engineer, Backend Developer, Fitness Domain Architect  

---

## 1. Executive Summary & Product Vision

The **AI Workout Coach** is an agentic fitness companion designed to provide evidence-based, personalized workout planning, intelligent session tracking, and adaptive coaching. Unlike superficial text-generation chatbots, the AI Workout Coach operates **agent-first**:
1. Grounded in a verified, structured exercise library.
2. Backed by transactional persistence for profiles, plans, and session logs.
3. Driven by deterministic fitness calculations for volume, progression, and consistency.
4. Bound by strict algorithmic safety guardrails against injury contraindications and red-flag symptoms.

---

## 2. Target Users & Core Personas

1. **The Busy Professional (Beginner to Intermediate):** Needs structured, time-efficient home or gym routines (30–45 mins) adapted to limited equipment (e.g., dumbbells, resistance bands, or bodyweight).
2. **The Progressive Strength Trainee (Intermediate to Advanced):** Requires systematic volume and overload tracking (sets, reps, weight, RPE) and periodized adjustments.
3. **The Returning Trainee (Rehabilitation / Injury-Aware):** Needs workout routines strictly filtered around sensitive joints or previous injuries (e.g., lower back pain, shoulder impingement, knee discomfort).

---

## 3. Core User Journeys (MVP Scope)

### Journey A: Create / Update Fitness Profile
* **User inputs:**
  * Primary Goal: `strength`, `hypertrophy` (muscle gain), `general_fitness`, `endurance`, or `weight_management`.
  * Experience Level: `beginner`, `intermediate`, or `advanced`.
  * Available Equipment: Array of items (e.g., `["bodyweight", "dumbbells", "barbell", "cable", "pull_up_bar"]`).
  * Schedule & Duration: Available training days per week (e.g., 3–5 days) and target session duration (e.g., 45 minutes).
  * Exercise Preferences: Preferred movement styles (e.g., compound lifts, calisthenics).
  * Medical Limitations & Injuries: Voluntarily declared constraints (e.g., `["lower_back_pain", "shoulder_impingement", "knee_pain"]`).
* **System Action:** Validates data schema, persists profile to relational store, sets baseline volume guidelines.

### Journey B: Generate Personalized Workout Plan
* **System Action:**
  * Evaluates goal, experience, available equipment, and schedule.
  * Filters candidate exercises to strictly exclude contraindications (e.g., substitutes Romanian Deadlift with Glute Bridge or Hip Thrust if lower back discomfort is flagged).
  * Organizes workouts across days (e.g., Push/Pull/Legs, Upper/Lower, or Full Body split).
  * Specifies exercise order (compounds before isolation), target sets, rep ranges, rest intervals, warm-up mobility, and cooldown.
  * Formulates explicit coaching rationale and approved equipment substitutions.
  * Validates plan against safety rules prior to persisting.

### Journey C: Log Completed Workout Session
* **User inputs:**
  * Session date, duration (minutes), perceived exertion rating (RPE 1–10).
  * Exercises completed, including set-by-set weight (kg/lbs) and repetitions achieved.
  * Skipped exercises and qualitative user feedback (e.g., "right shoulder felt tight during overhead press").
* **System Action:** Validates and stores immutable session records; updates progress metrics.

### Journey D: Analyze Progress & Adjust Plans
* **Deterministic Calculations:**
  * Workout completion rate and weekly adherence.
  * Total volume load ($Volume = \sum (\text{weight} \times \text{reps})$).
  * Estimated 1-Rep Max trends ($e1RM = \text{weight} \times (1 + \frac{\text{reps}}{30})$ for reps $\le 10$).
  * Comparison between planned target reps/weights and actual performance.
* **Intelligent Adaptation:**
  * If the user consistently hits top of rep ranges with low RPE $\rightarrow$ recommends incremental progressive overload (+2.5kg or +1-2 reps).
  * If user reports joint discomfort or fails target reps across 2+ sessions $\rightarrow$ recommends deload or swaps exercise variation.

### Journey E: Contextual Coaching Dialogue
* Multi-turn conversational interface where the coach can:
  * Answer technical technique questions ("How do I keep my wrists neutral during a bench press?").
  * Explain current training rationale ("Why are squats first on Day 1?").
  * Proactively query missing profile details or clarification on reported fatigue.
  * Immediately halt workouts upon detection of acute medical red flags (sharp pain, chest tightness, dizziness).

---

## 4. Safety, Ethics, and Guardrails

1. **Non-Medical Boundary:** The application provides general conditioning education, never medical diagnosis or rehabilitation therapy.
2. **Red-Flag Interception:** Keywords indicating acute distress (`sharp pain`, `popping sound`, `chest pain`, `lightheaded`, `dizzy`, `numbness`) trigger immediate, prominent prompts to discontinue activity and consult medical professionals.
3. **Contraindication Filtering:** Exercises tagged with biomechanical stress vectors are automatically suppressed when matching user limitations are present:
   * `lower_back_pain`: Excludes heavy spinal loading (e.g., Deadlift, Barbell Good Mornings, heavy Bent-over Rows) in favor of Chest-Supported Rows, Romanian Deadlifts with light DBs, or Leg Press.
   * `knee_pain`: Excludes deep knee flexion under load (e.g., Sissy Squats, Pistol Squats, Jump Squats) in favor of Box Squats, Romanian Deadlifts, and Glute Bridges.
   * `shoulder_impingement`: Excludes behind-the-neck presses, upright rows, and deep dips in favor of Neutral-Grip Dumbbell Press and Landmine Press.
4. **Volume Ceiling Safeguards:** Maximum weekly set limits per muscle group (Beginner: 8–12 sets; Intermediate: 12–16 sets; Advanced: 16–22 sets) to prevent overtraining.

---

## 5. Scope Boundaries

| In MVP Scope | Out of Scope (Future Roadmap) |
|---|---|
| User profile management with injury flags | Wearable integration (Apple Health, Garmin, Whoop) |
| Curated exercise library with muscle targets & equipment | Computer vision / camera rep counting / video form checks |
| Structured workout plan generation & validation | Dietary meal planning & calorie/macro tracking |
| Completed session & set-level logging | Subscription billing, payment processing, paywalls |
| Deterministic volume & progress calculation | Social feeds, leaderboards, and community sharing |
| Dynamic workout plan adjustments | Multi-agent hierarchical agent swarms |
| Conversational coaching interface with safety filters | Native mobile iOS/Android apps (PWA / Responsive Web first) |

---

## 6. Acceptance Criteria

1. **End-to-End Execution:** System runs locally via single command (`python main.py` or `pytest`).
2. **Data Consistency:** Profile creation, workout planning, and session logging persist across application restarts.
3. **Deterministic Math:** Progress volume and adherence calculations are mathematically verified with 100% precision.
4. **Guardrail Enforcement:** User declaring lower back pain receives zero contraindicated exercises in generated plans.
5. **Zero Token Failure:** System functions reliably with local mock model adapter during tests, and integrates seamlessly with Gemini 2.5/3.8 Flash via Vertex AI when credentials are provided.
