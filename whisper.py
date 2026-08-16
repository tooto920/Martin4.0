"""
Faster-Whisper STT provider implementation for Martin.
"""
import asyncio
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path

import sounddevice as sd
from faster_whisper import WhisperModel

from app.core.config import get_config
from app.core.exceptions import VoiceError
from app.core.logger import get_logger
from app.voice.stt import STTProvider, STTResult

logger = get_logger(__name__)


class FasterWhisperProvider(STTProvider):
    """Faster-Whisper STT provider for local speech recognition."""

    def __init__(self) -> None:
        config = get_config()
        self._model_name = config.get("voice", "stt", "model", default="base")
        self._language = config.get("voice", "stt", "language", default="cs")
        self._device = config.get("voice", "stt", "device", default="cpu")
        self._compute_type = config.get("voice", "stt", "compute_type", default="int8")
        self._model: WhisperModel | None = None
        self._stream: sd.InputStream | None = None
        self._is_listening = False

    @property
    def provider_name(self) -> str:
        return "faster-whisper"

    async def is_available(self) -> bool:
        """Check if model can be loaded."""
        try:
            await self._load_model()
            return True
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Faster-Whisper not available: {e}")
            return False

    async def _load_model(self) -> WhisperModel:
        """Load Whisper model."""
        if self._model is not None:
            return self._model

        try:
            self._model = await asyncio.to_thread(
                WhisperModel,
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
            )
            return self._model
        except Exception as e:  # noqa: BLE001
            raise VoiceError(f"Failed to load Whisper model: {e}")

    async def transcribe(self, audio_data: bytes, sample_rate: int) -> STTResult:
        """Transcribe audio data to text."""
        try:
            model = await self._load_model()

            # Write audio to temp file for transcription
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                # Convert raw bytes to wav format
                import wave
                with wave.open(f.name, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
                temp_path = f.name

            try:
                segments, info = await asyncio.to_thread(
                    model.transcribe,
                    temp_path,
                    language=self._language if self._language != "auto" else None,
                )

                text = " ".join(segment.text for segment in segments).strip()

                return STTResult(
                    text=text,
                    language=info.language,
                    confidence=None,  # faster-whisper doesn't provide confidence
                    is_final=True,
                )
            finally:
                Path(temp_path).unlink(missing_ok=True)

        except VoiceError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Transcription failed: {e}")
            raise VoiceError(f"Transcription failed: {e}")

    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[STTResult]:
        """Transcribe streaming audio to text."""
        # For now, collect chunks and transcribe periodically
        # A full streaming implementation would use VAD and streaming API
        buffer = bytearray()
        chunk_count = 0

        async for chunk in audio_stream:
            buffer.extend(chunk)
            chunk_count += 1

            # Transcribe every ~5 seconds of audio (at 16kHz, 16-bit mono)
            if chunk_count >= 50:  # Approximate
                audio_data = bytes(buffer)
                buffer.clear()
                chunk_count = 0

                try:
                    result = await self.transcribe(audio_data, 16000)
                    if result.text:
                        yield result
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Stream transcription error: {e}")

    async def get_supported_languages(self) -> list[str]:
        """Get supported languages."""
        # Whisper supports many languages
        return [
            "cs", "en", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "nl", "pl", "tr", "sv", "da", "no", "fi", "el",
        ]

    async def start_listening(self, callback) -> None:
        """Start continuous listening from microphone."""
        if self._is_listening:
            return

        self._is_listening = True

        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio input status: {status}")
            # Process audio in callback
            asyncio.create_task(callback(bytes(indata)))

        try:
            self._stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype="int16",
                callback=audio_callback,
            )
            self._stream.start()
            logger.info("Microphone listening started")
        except Exception as e:  # noqa: BLE001
            self._is_listening = False
            raise VoiceError(f"Failed to start microphone: {e}")

    async def stop_listening(self) -> None:
        """Stop listening."""
        self._is_listening = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Microphone listening stopped")