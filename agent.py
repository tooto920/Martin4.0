"""
Martin AI Agent - orchestrates conversation, tools, and memory.
"""
from typing import Any

from app.ai.ollama import OllamaProvider
from app.ai.prompts import get_full_system_prompt
from app.ai.provider import AIProvider, Message
from app.core.events import get_event_bus
from app.core.exceptions import AIProviderError
from app.core.logger import get_logger
from app.core.tools import get_tool_registry

logger = get_logger(__name__)


class MartinAgent:
    """Main AI agent that handles conversation flow."""

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or OllamaProvider()
        self._tool_registry = get_tool_registry()
        self._event_bus = get_event_bus()
        self._conversation: list[Message] = []
        self._system_prompt = get_full_system_prompt()
        self._max_iterations = 5

    @property
    def provider(self) -> AIProvider:
        return self._provider

    async def initialize(self) -> bool:
        """Initialize the agent and check provider availability."""
        available = await self._provider.is_available()
        if not available:
            logger.error(f"Provider {self._provider.provider_name} not available")
        return available

    def _build_messages(self, user_input: str) -> list[Message]:
        """Build message history for the provider."""
        messages = [Message(role="system", content=self._system_prompt)]
        messages.extend(self._conversation)
        messages.append(Message(role="user", content=user_input))
        return messages

    async def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[Message]:
        """Execute tool calls and return tool result messages."""
        tool_messages = []

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            name = function.get("name")
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            logger.info(f"Executing tool: {name} with args: {arguments}")
            result = self._tool_registry.execute(name, **arguments)

            tool_messages.append(Message(
                role="tool",
                content=result.error if not result.success and result.error else str(result.data),
                tool_call_id=tool_call.get("id"),
            ))

            if result.requires_confirmation:
                # In a real implementation, this would wait for user confirmation
                logger.warning(f"Tool {name} requires confirmation: {result.confirmation_message}")

        return tool_messages

    async def chat(self, user_input: str) -> str:
        """Process user input and return assistant response."""
        self._event_bus.publish("user_message", content=user_input)

        messages = self._build_messages(user_input)
        tools = self._tool_registry.get_schemas()

        for iteration in range(self._max_iterations):
            try:
                response = await self._provider.chat(messages, tools)
            except AIProviderError as e:
                logger.error(f"AI provider error: {e}")
                return "Omlouvám se, došlo k chybě při komunikaci s AI modelem."

            if response.tool_calls:
                messages.append(Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                ))

                tool_messages = await self._execute_tool_calls(response.tool_calls)
                messages.extend(tool_messages)
                continue

            assistant_response = response.content
            self._conversation.append(Message(role="user", content=user_input))
            self._conversation.append(Message(role="assistant", content=assistant_response))

            self._event_bus.publish("assistant_message", content=assistant_response)
            return assistant_response

        return "Omlouvám se, dosáhl jsem maximálního počtu iterací."

    def clear_history(self) -> None:
        """Clear conversation history."""
        self._conversation.clear()

    def get_history(self) -> list[Message]:
        """Get conversation history."""
        return self._conversation.copy()


import json