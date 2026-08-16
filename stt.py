"""
STT Provider abstraction for Martin.
Defines the interface for speech-to-text providers.
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class STTResult:
    """Result of STT transcription."""
    text: str
    language: str | None = None
    confidence: float | None = None
    is_final: bool = True


class STTProvider(ABC):
    """Abstract base class for STT providers."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes, sample_rate: int) -> STTResult:
        """Transcribe audio data to text."""

    @abstractmethod
    def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[STTResult]:
        """Transcribe streaming audio to text."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""

    @abstractmethod
    async def get_supported_languages(self) -> list[str]:
        """Get supported languages."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
