"""
AI Provider abstraction for Martin.
Defines the interface for LLM providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """Chat message."""
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


@dataclass
class ChatResponse:
    """Response from chat completion."""
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str = "stop"
    usage: dict[str, int] | None = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """Send chat completion request."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Get model name."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
