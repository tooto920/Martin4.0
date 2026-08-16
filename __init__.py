"""
Voice package for Martin.
"""
from __future__ import annotations

__all__ = [
    "FasterWhisperProvider",
    "PiperTTSProvider",
    "STTProvider",
    "STTResult",
    "TTSProvider",
    "TTSResult",
    "TTSVoice",
]


def __getattr__(name: str):
    if name in __all__:
        try:
            if name == "FasterWhisperProvider":
                from app.voice.whisper import FasterWhisperProvider
                return FasterWhisperProvider
            if name == "PiperTTSProvider":
                from app.voice.piper import PiperTTSProvider
                return PiperTTSProvider
            if name in {"STTProvider", "STTResult"}:
                from app.voice.stt import STTProvider, STTResult
                if name == "STTProvider":
                    return STTProvider
                return STTResult
            if name in {"TTSProvider", "TTSResult", "TTSVoice"}:
                from app.voice.tts import TTSProvider, TTSResult, TTSVoice
                if name == "TTSProvider":
                    return TTSProvider
                if name == "TTSResult":
                    return TTSResult
                return TTSVoice
        except Exception as exc:  # noqa: BLE001
            raise ImportError(f"Voice dependency missing for {name}: {exc}") from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
