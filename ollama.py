"""
Ollama AI provider implementation for Martin.
"""
import asyncio
from typing import Any

import httpx

from app.ai.provider import AIProvider, ChatResponse, Message
from app.core.config import get_config
from app.core.exceptions import AIProviderError
from app.core.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(AIProvider):
    """Ollama provider for local LLM inference."""

    def __init__(self) -> None:
        config = get_config()
        self._base_url = config.get("ai", "ollama_url", default="http://localhost:11434")
        self._model = config.get("ai", "model", default="gemma3:4b")
        self._client: httpx.AsyncClient | None = None

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def _get_client_for_loop(self) -> httpx.AsyncClient:
        try:
            loop = asyncio.get_running_loop()
            if self._client is None:
                self._client = httpx.AsyncClient(timeout=120.0)
            elif isinstance(self._client, httpx.AsyncClient) and getattr(self._client, '_loop', None) is not loop:
                await self._client.aclose()
                self._client = httpx.AsyncClient(timeout=120.0)
        except RuntimeError:
            if self._client is None:
                self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    async def is_available(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            client = await self._get_client_for_loop()
            response = await client.get(f"{self._base_url}/api/tags")
            if response.status_code != 200:
                return False
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return self._model in models
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        """Send chat completion request to Ollama."""
        client = await self._get_client_for_loop()

        ollama_messages = []
        for msg in messages:
            ollama_msg: dict[str, Any] = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                ollama_msg["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                ollama_msg["tool_call_id"] = msg.tool_call_id
            ollama_messages.append(ollama_msg)

        payload = {
            "model": self._model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            message = data.get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls")

            return ChatResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=data.get("done_reason", "stop"),
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
            )

        except httpx.HTTPStatusError as e:
            raise AIProviderError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except (httpx.RequestError, ValueError) as e:
            raise AIProviderError(f"Ollama request failed: {e}")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None