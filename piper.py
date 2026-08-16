"""
Piper TTS provider implementation for Martin.
"""
import asyncio
import json
from pathlib import Path

import sounddevice as sd
from piper import PiperVoice

from app.core.config import get_config
from app.core.exceptions import VoiceError
from app.core.logger import get_logger
from app.voice.tts import TTSProvider, TTSResult, TTSVoice

logger = get_logger(__name__)


class PiperTTSProvider(TTSProvider):
    """Piper TTS provider for local speech synthesis."""

    def __init__(self) -> None:
        config = get_config()
        self._voice_name = config.get("voice", "tts", "voice", default="cs_CZ-jirka-medium")
        self._speed = config.get("voice", "tts", "speed", default=1.0)
        self._models_dir = Path(config.get("data", "models_dir", default="data/models/tts"))
        self._voice: PiperVoice | None = None
        self._stream: sd.OutputStream | None = None
        self._playback_task: asyncio.Task | None = None
        self._is_playing = False

    @property
    def provider_name(self) -> str:
        return "piper"

    async def is_available(self) -> bool:
        """Check if Piper voice model is available."""
        model_path = self._models_dir / f"{self._voice_name}.onnx"
        config_path = self._models_dir / f"{self._voice_name}.onnx.json"
        return model_path.exists() and config_path.exists()

    async def _load_voice(self) -> PiperVoice:
        """Load Piper voice model."""
        if self._voice is not None:
            return self._voice

        model_path = self._models_dir / f"{self._voice_name}.onnx"
        config_path = self._models_dir / f"{self._voice_name}.onnx.json"

        if not model_path.exists():
            raise VoiceError(f"Piper voice model not found: {model_path}")
        if not config_path.exists():
            raise VoiceError(f"Piper voice config not found: {config_path}")

        try:
            self._voice = await asyncio.to_thread(
                PiperVoice.load, str(model_path), str(config_path)
            )
            return self._voice
        except Exception as e:  # noqa: BLE001
            raise VoiceError(f"Failed to load Piper voice: {e}")

    async def synthesize(self, text: str, voice_id: str | None = None) -> TTSResult:
        """Synthesize text to speech using Piper."""
        if not text.strip():
            return TTSResult(success=False, error="Empty text")

        try:
            voice = await self._load_voice()

            # Synthesize in a thread to avoid blocking
            audio_chunks = []
            length_scale = 1.0 / self._speed
            for chunk in await asyncio.to_thread(
                lambda: voice.synthesize(text, length_scale=length_scale)  # type: ignore[call-arg]
            ):
                audio_chunks.append(chunk)  # noqa: PERF402

            audio_data = b"".join(audio_chunks)  # type: ignore[arg-type]
            sample_rate = voice.config.sample_rate

            return TTSResult(
                success=True,
                audio_data=audio_data,
                sample_rate=sample_rate,
            )

        except VoiceError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"Piper synthesis failed: {e}")
            return TTSResult(success=False, error=str(e))

    async def get_voices(self) -> list[TTSVoice]:
        """Get available voices."""
        voices: list[TTSVoice] = []
        if not self._models_dir.exists():
            return voices

        for model_file in self._models_dir.glob("*.onnx"):
            config_file = self._models_dir / f"{model_file.stem}.json"
            if config_file.exists():
                try:
                    def _load_config(path: Path) -> dict:
                        with open(path, "r", encoding="utf-8") as f:
                            return json.load(f)

                    config = await asyncio.to_thread(_load_config, config_file)
                    voice_info = config.get("voice_info", {})
                    voices.append(TTSVoice(
                        id=model_file.stem,
                        name=voice_info.get("name", model_file.stem),
                        language=voice_info.get("language", "unknown"),
                        gender=voice_info.get("gender", "unknown"),
                        quality=voice_info.get("quality", "medium"),
                        sample_rate=voice_info.get("sample_rate", 22050),
                    ))
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to read voice config {config_file}: {e}")

        return voices

    async def play_audio(self, audio_data: bytes, sample_rate: int) -> None:
        """Play audio data using sounddevice."""
        if self._is_playing:
            await self.stop_playback()

        self._is_playing = True

        def _play():
            try:
                self._stream = sd.OutputStream(
                    samplerate=sample_rate,
                    channels=1,
                    dtype="int16",
                )
                self._stream.start()
                self._stream.write(audio_data)
                self._stream.stop()
                self._stream.close()
                self._stream = None
            except Exception as e:  # noqa: BLE001
                logger.error(f"Audio playback failed: {e}")
            finally:
                self._is_playing = False

        self._playback_task = asyncio.create_task(asyncio.to_thread(_play))
        await self._playback_task

    async def stop_playback(self) -> None:
        """Stop current audio playback."""
        self._is_playing = False
        if self._stream:
            try:
                self._stream.abort()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to abort stream: {e}")
        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()
            try:
                await self._playback_task
            except asyncio.CancelledError:
                pass
        self._playback_task = None
        self._stream = None