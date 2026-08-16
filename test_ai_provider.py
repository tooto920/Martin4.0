"""
Tests for AI provider abstraction.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.ai.ollama import OllamaProvider
from app.ai.provider import AIProvider, ChatResponse, Message
from app.core.config import Config


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset config singleton before each test."""
    Config._instance = None
    Config._config = {}
    Config._loaded = False
    Config._config_path = None
    Config().set_config_for_testing({
        "ai": {
            "provider": "ollama",
            "model": "gemma3:4b",
            "ollama_url": "http://localhost:11434",
            "temperature": 0.7,
            "max_tokens": 2048,
        }
    })


class MockProvider(AIProvider):
    """Mock provider for testing."""

    def __init__(self) -> None:
        self._model = "test-model"
        self._available = True
        self.chat_mock = AsyncMock()

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "mock"

    async def is_available(self) -> bool:
        return self._available

    async def chat(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatResponse:
        return await self.chat_mock(messages, tools, temperature, max_tokens)


class TestAIProvider:
    """Tests for AI provider abstraction."""

    @pytest.mark.asyncio
    async def test_provider_interface(self) -> None:
        """Provider should implement required interface."""
        provider = MockProvider()
        provider._available = True

        assert await provider.is_available() is True
        assert provider.model == "test-model"
        assert provider.provider_name == "mock"

    @pytest.mark.asyncio
    async def test_chat_response_structure(self) -> None:
        """Chat should return structured response."""
        provider = MockProvider()
        provider.chat_mock.return_value = ChatResponse(
            content="Test response",
            finish_reason="stop",
        )

        messages = [Message(role="user", content="Hello")]
        response = await provider.chat(messages)

        assert isinstance(response, ChatResponse)
        assert response.content == "Test response"
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_with_tools(self) -> None:
        """Chat should accept tools parameter."""
        provider = MockProvider()
        provider.chat_mock.return_value = ChatResponse(content="OK")

        tools = [{"name": "test", "description": "Test tool"}]
        messages = [Message(role="user", content="Hello")]

        await provider.chat(messages, tools=tools)

        provider.chat_mock.assert_called_once()
        call_args = provider.chat_mock.call_args
        # tools can be in kwargs or args (positional)
        if "tools" in call_args.kwargs:
            assert call_args.kwargs["tools"] == tools
        else:
            # Check positional args: (messages, tools, temperature, max_tokens)
            assert len(call_args.args) >= 2
            assert call_args.args[1] == tools

    @pytest.mark.asyncio
    async def test_chat_with_tool_calls(self) -> None:
        """Chat should handle tool calls in response."""
        provider = MockProvider()
        provider.chat_mock.return_value = ChatResponse(
            content="",
            tool_calls=[{"id": "1", "function": {"name": "test", "arguments": "{}"}}],
        )

        messages = [Message(role="user", content="Hello")]
        response = await provider.chat(messages)

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1


class TestOllamaProvider:
    """Tests for Ollama provider (mocked)."""

    @pytest.mark.asyncio
    async def test_init(self) -> None:
        """Should initialize with config values."""
        with patch("app.ai.ollama.get_config") as mock_config:
            mock_config.return_value.get.side_effect = lambda *keys, default=None: {
                ("ai", "ollama_url"): "http://custom:11434",
                ("ai", "model"): "custom-model",
            }.get(keys, default)

            provider = OllamaProvider()
            assert provider._base_url == "http://custom:11434"
            assert provider._model == "custom-model"

    @pytest.mark.asyncio
    async def test_is_available_success(self) -> None:
        """Should return True when Ollama is available with model."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "gemma3:4b"}]}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        provider._client = mock_client

        result = await provider.is_available()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_available_model_missing(self) -> None:
        """Should return False when model not found."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other-model"}]}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        provider._client = mock_client

        result = await provider.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_connection_error(self) -> None:
        """Should return False on connection error."""
        provider = OllamaProvider()

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("Connection refused")
        provider._client = mock_client

        result = await provider.is_available()
        assert result is False