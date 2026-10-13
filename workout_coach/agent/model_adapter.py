"""Pluggable Model Adapters: Abstract Base, Deterministic Mock, and Vertex AI Gemini."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os
import json
import logging
import re

from workout_coach.core.maps_service import GoogleMapsService

logger = logging.getLogger("workout_coach.agent.model_adapter")


def _build_plan_a2ui(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build an A2UI v0.8 surface for a generated workout plan."""
    components = []
    child_ids = []

    header_id = "plan_header"
    components.append({
        "id": header_id,
        "component": {
            "Text": {
                "text": {"literalString": f"🎯 {plan['plan_name']}"},
                "usageHint": "h2"
            }
        }
    })
    child_ids.append(header_id)

    badge_id = "plan_badge"
    components.append({
        "id": badge_id,
        "component": {
            "Text": {
                "text": {"literalString": f"Split: {plan['split_type'].replace('_', ' ').title()} • Frequency: {plan['days_per_week']} Days/Week"},
                "usageHint": "caption"
            }
        }
    })
    child_ids.append(badge_id)

    components.append({"id": "plan_div", "component": {"Divider": {}}})
    child_ids.append("plan_div")

    for s in plan.get("sessions", [])[:4]:
        s_title_id = f"sess_{s['day_number']}_title"
        components.append({
            "id": s_title_id,
            "component": {
                "Text": {
                    "text": {"literalString": f"⚡ {s['day_name']} — {s.get('focus', '')}"},
                    "usageHint": "h4"
                }
            }
        })
        child_ids.append(s_title_id)

        ex_summary = ", ".join(e["exercise_name"] for e in s.get("exercises", [])[:3])
        s_desc_id = f"sess_{s['day_number']}_desc"
        components.append({
            "id": s_desc_id,
            "component": {
                "Text": {
                    "text": {"literalString": f"Exercises: {ex_summary}..."},
                    "usageHint": "body"
                }
            }
        })
        child_ids.append(s_desc_id)

    col_id = "plan_col"
    components.append({
        "id": col_id,
        "component": {
            "Column": {
                "children": {"explicitList": child_ids}
            }
        }
    })

    card_id = "plan_card"
    components.append({
        "id": card_id,
        "component": {
            "Card": {
                "child": col_id
            }
        }
    })

    return [
        {"beginRendering": {"root": card_id}},
        {"surfaceUpdate": {"components": components}}
    ]


class BaseModelAdapter(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate_reply(
        self,
        user_message: str,
        user_id: str,
        chat_history: List[Dict[str, Any]],
        system_prompt: str,
        tool_executor: Any
    ) -> Dict[str, Any]:
        """Generate response and execute necessary tools."""
        pass


class MockWorkoutCoachModelAdapter(BaseModelAdapter):
    """Deterministic, offline-capable model adapter for reliable unit & integration tests."""

    def generate_reply(
        self,
        user_message: str,
        user_id: str,
        chat_history: List[Dict[str, Any]],
        system_prompt: str,
        tool_executor: Any
    ) -> Dict[str, Any]:
        msg_lower = user_message.lower().strip()
        executed_tools: List[Dict[str, Any]] = []

        # 1. Profile Creation / Query Intent
        # Match if explicitly mentions 'profile' or states fitness onboarding parameters (goal, equipment, days/week)
        is_profile_intent = (
            "profile" in msg_lower
            or any(k in msg_lower for k in ["i want to build", "my goal is", "set my goal", "training days", "days a week"])
        )

        if is_profile_intent:
            if any(k in msg_lower for k in ["create", "set", "make", "build", "want to", "goal", "training", "days"]):
                # Extract goal
                if "strength" in msg_lower:
                    goal = "strength"
                elif "muscle" in msg_lower or "hypertrophy" in msg_lower:
                    goal = "muscle_gain"
                elif "endurance" in msg_lower:
                    goal = "endurance"
                else:
                    goal = "general_fitness"

                # Extract equipment
                equip = ["bodyweight"]
                if "dumbbell" in msg_lower:
                    equip.append("dumbbells")
                if "barbell" in msg_lower:
                    equip.append("barbell")
                if "bench" in msg_lower:
                    equip.append("bench")
                if "pull up" in msg_lower or "pull-up" in msg_lower:
                    equip.append("pull_up_bar")

                # Extract days per week
                days = 3
                days_match = re.search(r"(\d+)\s*days", msg_lower)
                if days_match:
                    days = int(days_match.group(1))

                # Extract limitations
                limitations = []
                if "lower back" in msg_lower or "back pain" in msg_lower:
                    limitations.append("lower_back_pain")
                if "knee" in msg_lower:
                    limitations.append("knee_pain")
                if "shoulder" in msg_lower:
                    limitations.append("shoulder_impingement")

                res = tool_executor.update_fitness_profile(
                    user_id=user_id,
                    fitness_goal=goal,
                    available_equipment=equip,
                    days_per_week=days,
                    limitations=limitations
                )
                executed_tools.append({"tool": "update_fitness_profile", "result": res})
                reply = f"I've configured your fitness profile! Goal: {goal}, Training: {days} days/week, Equipment: {', '.join(equip)}."
                if limitations:
                    reply += f" I noted your limitation: {', '.join(limitations)} and will avoid contraindicated exercises."
                return {
                    "reply": reply,
                    "intent": "update_profile",
                    "executed_tools": executed_tools,
                    "suggested_actions": ["Create my workout plan", "Search exercises"]
                }
            else:
                res = tool_executor.get_fitness_profile(user_id=user_id)
                executed_tools.append({"tool": "get_fitness_profile", "result": res})
                if res.get("status") == "success":
                    prof = res["profile"]
                    reply = (
                        f"Your profile: Goal is {prof['fitness_goal']}, training {prof['days_per_week']} days/week "
                        f"with {', '.join(prof['available_equipment'])}. Limitations: {', '.join(prof['limitations']) or 'None'}."
                    )
                else:
                    reply = "You don't have a profile yet. Would you like me to set one up with your goals and available equipment?"
                return {
                    "reply": reply,
                    "intent": "get_profile",
                    "executed_tools": executed_tools,
                    "suggested_actions": ["Create a workout plan"]
                }

        # 2. Workout Plan Generation Intent
        if any(k in msg_lower for k in ["plan", "routine", "program", "workout plan"]):
            if any(k in msg_lower for k in ["create", "generate", "make", "build", "new"]):
                res = tool_executor.create_workout_plan(user_id=user_id)
                executed_tools.append({"tool": "create_workout_plan", "result": res})
                if res.get("status") == "success":
                    p = res["plan"]
                    reply = (
                        f"🎯 Generated your customized {p['plan_name']}! It is a {p['split_type'].replace('_', ' ')} "
                        f"split across {p['days_per_week']} days per week. {p['rationale']}"
                    )
                    a2ui_surface = _build_plan_a2ui(p)
                    return {
                        "reply": reply,
                        "intent": "create_plan",
                        "executed_tools": executed_tools,
                        "suggested_actions": ["View today's exercises", "Log a completed workout", "Find gyms near me"],
                        "a2ui_messages": a2ui_surface
                    }
                else:
                    reply = f"Could not generate plan: {res.get('message')}"
                    return {
                        "reply": reply,
                        "intent": "create_plan",
                        "executed_tools": executed_tools,
                        "suggested_actions": ["View today's exercises", "Log a completed workout"]
                    }
            else:
                res = tool_executor.get_current_workout_plan(user_id=user_id)
                executed_tools.append({"tool": "get_current_workout_plan", "result": res})
                if res.get("status") == "success":
                    p = res["plan"]
                    reply = f"Your active plan is {p['plan_name']} ({p['days_per_week']} days/week). Ready for your next session?"
                else:
                    reply = "You don't have an active plan yet. Tell me 'generate a workout plan' to get started!"
                return {
                    "reply": reply,
                    "intent": "get_plan",
                    "executed_tools": executed_tools,
                    "suggested_actions": ["Generate my workout plan"]
                }

        # 3. Exercise Search Intent
        if any(k in msg_lower for k in ["exercise", "substitute", "how to", "bench press", "squat", "pushup"]):
            res = tool_executor.search_exercises(query=user_message)
            executed_tools.append({"tool": "search_exercises", "result": res})
            if res.get("count", 0) > 0:
                top_ex = res["exercises"][0]
                reply = f"**{top_ex['name']}** ({top_ex['category'].upper()}): {top_ex['instructions']}"
            else:
                reply = "I searched our exercise library but didn't find an exact match. Let me know which muscle group or movement you'd like to work."
            return {
                "reply": reply,
                "intent": "search_exercise",
                "executed_tools": executed_tools,
                "suggested_actions": ["Show exercise substitutions"]
            }

        # 4. Progress & History Intent
        if any(k in msg_lower for k in ["progress", "history", "trend", "consistency", "volume"]):
            res = tool_executor.calculate_progress(user_id=user_id)
            executed_tools.append({"tool": "calculate_progress", "result": res})
            if res.get("status") == "success":
                m = res["metrics"]
                adj_text = " ".join(m["recommended_adjustments"])
                reply = (
                    f"📊 Progress Summary: You've completed {m['total_completed_sessions']} sessions with "
                    f"{m['weekly_adherence_rate'] * 100:.0f}% adherence and {m['total_volume_kg']:.1f}kg total volume load. "
                    f"Recommendation: {adj_text}"
                )
            else:
                reply = "No progress records found yet. Log a workout session to see your stats!"
            return {
                "reply": reply,
                "intent": "calculate_progress",
                "executed_tools": executed_tools,
                "suggested_actions": ["Log a workout session"]
            }

        # 5. Google Maps & Places Fitness Facility Scout
        if any(k in msg_lower for k in ["gym", "gyms", "track", "running", "calisthenic", "park", "facilities", "where can i workout", "where to workout", "place to workout", "place to work out", "find a place", "workout spot", "fitness center"]):
            # Extract facility type
            if "track" in msg_lower or "running" in msg_lower:
                ftype = "running track"
            elif "calisthenic" in msg_lower or "street workout" in msg_lower or "pull-up" in msg_lower or "park" in msg_lower:
                ftype = "calisthenics park"
            elif "powerlifting" in msg_lower or "olympic" in msg_lower or "barbell" in msg_lower:
                ftype = "powerlifting gym"
            else:
                ftype = "gym"

            # Extract location
            loc_match = re.search(r"(?:near|in|around|at)\s+([A-Za-z0-9\s,]+)", user_message, re.IGNORECASE)
            location = loc_match.group(1).strip() if loc_match else "Downtown Area"
            location = re.sub(r"\b(please|thanks|thank you|now|today|for me)\b", "", location, flags=re.IGNORECASE).strip()
            if not location:
                location = "Downtown Area"

            res = tool_executor.find_nearby_gyms(location=location, facility_type=ftype)
            executed_tools.append({"tool": "find_nearby_gyms", "result": res})
            venues = res.get("venues", [])

            lines = [f"📍 **Ronny's Facility Scout (Google Maps)**"]
            lines.append(f"Found {len(venues)} top-rated **{ftype}** locations near **{location}**:")
            for v in venues:
                lines.append(f"- **{v['name']}** (★ {v['rating']}) — *{v.get('highlight', '')}*")
                lines.append(f"  📌 Address: {v['address']}")
                lines.append(f"  🗺️ [View on Google Maps]({v['google_maps_url']}) | [Get Directions]({v['directions_url']})")

            a2ui_surface = GoogleMapsService.build_a2ui_surface(venues, location, ftype)

            return {
                "reply": "\n".join(lines),
                "intent": "find_nearby_gyms",
                "executed_tools": executed_tools,
                "suggested_actions": ["Get directions to nearest gym", "Check outdoor running tracks", "Generate my workout plan"],
                "a2ui_messages": a2ui_surface,
                "maps_data": res
            }

        # 6. Default Contextual Coaching Reply (Ronny Persona)
        return {
            "reply": (
                "Hey athlete! I am Ronny, your personal fitness coach. "
                "I can build you a tailored strength program, find alternative exercises for any injuries or limitations, "
                "scout nearby gyms and tracks with Google Maps, and track your progressive overload milestones. "
                "How can we level up your training today?"
            ),
            "intent": "general_coaching",
            "executed_tools": executed_tools,
            "suggested_actions": ["Create my fitness profile", "Generate a workout plan", "Find gyms near me"]
        }


class GeminiVertexModelAdapter(BaseModelAdapter):
    """Live Google Cloud Vertex AI Gemini model adapter."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1", model_name: str = "gemini-2.5-flash"):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-04-9ecf92a8e298")
        self.location = location
        self.model_name = model_name
        self.fallback = MockWorkoutCoachModelAdapter()

    def generate_reply(
        self,
        user_message: str,
        user_id: str,
        chat_history: List[Dict[str, Any]],
        system_prompt: str,
        tool_executor: Any
    ) -> Dict[str, Any]:
        try:
            from google import genai
            client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
            
            # Format conversational prompt
            prompt = f"System: {system_prompt}\nUser ID: {user_id}\nUser Message: {user_message}"
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            reply_text = response.text if hasattr(response, "text") and response.text else "Received response from Gemini."
            return {
                "reply": reply_text,
                "intent": "gemini_generative",
                "executed_tools": [],
                "suggested_actions": ["Check my workout plan", "Log session"]
            }
        except Exception as e:
            logger.warning("Vertex AI Gemini call failed or credentials unconfigured, using deterministic adapter: %s", str(e))
            result = self.fallback.generate_reply(user_message, user_id, chat_history, system_prompt, tool_executor)
            result["reply"] = f"{result['reply']} *(Offline Coach Adapter)*"
            return result
