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

        # Memory / Conversation Recall Intent
        if any(k in msg_lower for k in ["what did we discuss", "what did we talk about", "remember", "earlier", "previous message", "what was my goal"]):
            if chat_history:
                recent_topics = [m.get("content", "") for m in chat_history if m.get("role") == "user"]
                last_topic = recent_topics[-1] if recent_topics else "our previous workout discussions"
                reply = f"Earlier we discussed: \"{last_topic}\". I have your training context in mind — how would you like to build on that today?"
            else:
                reply = "We just started our session! You can tell me your fitness goals, ask to build a workout plan, or search for nearby gyms."
            return {
                "reply": reply,
                "intent": "memory_recall",
                "executed_tools": executed_tools,
                "suggested_actions": ["Review my active plan", "Find gyms near me"]
            }

        # Plateau / Sticking Point Intent
        if any(k in msg_lower for k in ["stuck at", "plateau", "can't increase", "cant increase", "stuck for"]):
            reply = (
                "Breaking through a strength plateau requires systematic stimulus variation:\n\n"
                "1. **Microloading**: Use smaller increments (+1.25kg to 2.5kg total) to continue progressive overload without breaking form.\n"
                "2. **Pause Reps**: Add a 2-second pause at the chest/bottom position to eliminate stretch reflex and build explosive starting power.\n"
                "3. **Volume Wave**: Alternate heavy days (3-5 reps at RPE 8-9) with moderate hypertrophy volume days (8-10 reps).\n"
                "4. **Recovery & Nutrition**: Ensure 7-8 hours of sleep and 1.6-2.0g/kg protein with a slight caloric surplus (+250 kcal/day)."
            )
            return {
                "reply": reply,
                "intent": "plateau_overload_coaching",
                "executed_tools": executed_tools,
                "suggested_actions": ["Log a workout session", "Search exercise library"]
            }

        # Nutrition / Bulking / Cutting Intent
        if any(k in msg_lower for k in ["keto", "carb cycling", "bulking", "cutting", "calories", "macros", "protein intake"]):
            reply = (
                "For gaining muscle (hypertrophy), carbohydrates are the premier glycolytic fuel for high-intensity lifting. "
                "While keto can be effective for rapid fat loss, carb cycling or consistent complex-carbohydrate intake around training windows "
                "is significantly superior for lifting performance, glycogen replenishment, and muscle protein synthesis.\n\n"
                "🎯 **Recommended Protocol**:\n"
                "• **Caloric Surplus**: +250-350 kcal/day above maintenance\n"
                "• **Protein**: 1.6 - 2.2 g per kg of body weight\n"
                "• **Carbohydrates**: 4 - 6 g per kg, clustered around pre- and post-workout windows\n"
                "• **Fats**: 0.8 - 1.0 g per kg for hormonal balance"
            )
            return {
                "reply": reply,
                "intent": "nutrition_coaching",
                "executed_tools": executed_tools,
                "suggested_actions": ["Generate my workout plan", "Log completed workout"]
            }

        # 3. Exercise Search Intent
        is_search_intent = (
            any(k in msg_lower for k in ["how to do", "instructions for", "show exercise", "substitute", "substitutions"])
            or (any(k in msg_lower for k in ["bench press", "squat", "deadlift", "pushup", "pullup"]) and not any(k in msg_lower for k in ["stuck", "plateau"]))
        )
        if is_search_intent:
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
        self.project_id = project_id or os.environ.get("PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-04-9ecf92a8e298")
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
        msg_lower = user_message.lower().strip()

        # Route facility search directly to Google Maps tool to preserve rich cards & coordinates
        if any(k in msg_lower for k in ["gym", "gyms", "track", "running", "calisthenic", "park", "facilities", "where can i workout", "where to workout", "place to workout", "place to work out", "find a place", "workout spot", "fitness center"]):
            return self.fallback.generate_reply(user_message, user_id, chat_history, system_prompt, tool_executor)

        # Route explicit workout plan generation to deterministic planner tool to emit A2UI card
        if any(k in msg_lower for k in ["plan", "routine", "program", "workout plan"]) and any(k in msg_lower for k in ["create", "generate", "make", "build", "new"]):
            return self.fallback.generate_reply(user_message, user_id, chat_history, system_prompt, tool_executor)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

            # Build enriched system instruction with athlete context
            athlete_context = f"Athlete ID: {user_id}"
            if hasattr(tool_executor, "repo"):
                try:
                    prof = tool_executor.repo.get_profile(user_id)
                    if prof:
                        athlete_context += f" | Goal: {prof.fitness_goal.value} | Level: {prof.experience_level.value} | Equipment: {', '.join(prof.available_equipment)} | Limitations: {', '.join(prof.limitations) if prof.limitations else 'None'}"
                except Exception:
                    pass

            full_system = (
                f"{system_prompt}\n\n"
                f"CURRENT ATHLETE CONTEXT:\n{athlete_context}\n\n"
                "Be direct, athletic, and evidence-based. If the athlete asks about plateau breaking, nutrition, or previous conversation, answer thoroughly and remember past messages."
            )

            # Multi-turn conversation history
            contents = []
            for m in (chat_history or []):
                role = "user" if m.get("role") == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m.get("content", ""))]))

            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=full_system,
                    temperature=0.7,
                    max_output_tokens=600
                )
            )

            reply_text = response.text if hasattr(response, "text") and response.text else "Let's keep training hard, athlete!"
            return {
                "reply": reply_text,
                "intent": "gemini_generative",
                "executed_tools": [],
                "suggested_actions": ["Check my workout plan", "Log session", "Find gyms near me"]
            }
        except Exception as e:
            logger.warning("Vertex AI Gemini call failed, falling back to deterministic adapter: %s", str(e))
            result = self.fallback.generate_reply(user_message, user_id, chat_history, system_prompt, tool_executor)
            return result
