"""
TTS Provider abstraction for Martin.
Defines the interface for text-to-speech providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSVoice:
    """TTS voice information."""
    id: str
    name: str
    language: str
    gender: str
    quality: str
    sample_rate: int = 22050


@dataclass
class TTSResult:
    """Result of TTS synthesis."""
    success: bool
    audio_data: bytes | None = None
    sample_rate: int = 22050
    error: str | None = None


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str | None = None) -> TTSResult:
        """Synthesize text to speech."""

    @abstractmethod
    async def get_voices(self) -> list[TTSVoice]:
        """Get available voices."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is available."""

    @abstractmethod
    async def play_audio(self, audio_data: bytes, sample_rate: int) -> None:
        """Play audio data."""

    @abstractmethod
    async def stop_playback(self) -> None:
        """Stop current audio playback."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
