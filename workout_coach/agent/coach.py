"""Central Coaching Agent Orchestrator."""

from typing import Optional, Dict, Any
from workout_coach.core.models import ChatTurnResponse
from workout_coach.core.repository import WorkoutRepository
from workout_coach.core.safety import scan_for_red_flags
from workout_coach.agent.tools import WorkoutCoachTools
from workout_coach.agent.model_adapter import BaseModelAdapter, MockWorkoutCoachModelAdapter

SYSTEM_PROMPT = """You are Ronny, Your Personal Fitness Coach — an elite, evidence-based AI workout and strength assistant.
Your role is to help athletes define their goals, build personalized training splits, find nearby gyms and training facilities using Google Maps, log workouts, and calculate progressive overload.
Always enforce safety: check declared limitations, avoid contraindicated movements, and never diagnose medical conditions.
Maintain an encouraging, disciplined, athletic coaching voice.
"""


class WorkoutCoach:
    """Agent orchestrating conversational turns, safety filters, tool execution, and persistence."""

    def __init__(
        self,
        repo: Optional[WorkoutRepository] = None,
        model_adapter: Optional[BaseModelAdapter] = None
    ):
        self.repo = repo or WorkoutRepository()
        self.tools = WorkoutCoachTools(self.repo)
        self.model_adapter = model_adapter or MockWorkoutCoachModelAdapter()

    def process_message(self, user_id: str, message: str) -> ChatTurnResponse:
        """Process incoming user turn through safety filtering, model reasoning, tool execution, and storage."""
        # 1. Pre-turn Safety Scan for Red-Flag Medical Symptoms
        warning = scan_for_red_flags(message)
        if warning:
            # Save message and warning response to history
            self.repo.save_chat_message(user_id=user_id, role="user", content=message)
            self.repo.save_chat_message(user_id=user_id, role="assistant", content=warning)
            return ChatTurnResponse(
                reply=warning,
                intent="medical_red_flag_intercepted",
                executed_tools=[],
                suggested_actions=["Rest and consult a physician", "Find gentle mobility movements"],
                safety_warning=warning
            )

        # 2. Retrieve recent chat history
        history = self.repo.get_chat_history(user_id=user_id, limit=6)

        # 3. Model Reasoning & Tool Execution
        output = self.model_adapter.generate_reply(
            user_message=message,
            user_id=user_id,
            chat_history=history,
            system_prompt=SYSTEM_PROMPT,
            tool_executor=self.tools
        )

        reply = output.get("reply", "I am ready to help with your workout.")
        intent = output.get("intent", "general")
        executed_tools = output.get("executed_tools", [])
        suggested_actions = output.get("suggested_actions", [])
        a2ui_messages = output.get("a2ui_messages")
        maps_data = output.get("maps_data")

        # 4. Persist messages
        self.repo.save_chat_message(user_id=user_id, role="user", content=message)
        self.repo.save_chat_message(
            user_id=user_id,
            role="assistant",
            content=reply,
            tool_calls=str(executed_tools) if executed_tools else None
        )

        return ChatTurnResponse(
            reply=reply,
            intent=intent,
            executed_tools=executed_tools,
            suggested_actions=suggested_actions,
            safety_warning=None,
            a2ui_messages=a2ui_messages,
            maps_data=maps_data
        )
