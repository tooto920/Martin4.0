"""
Chat page for Martin GUI.
"""
import asyncio
import threading
from datetime import datetime

import sounddevice as sd
from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ai.agent import MartinAgent
from app.ai.ollama import OllamaProvider
from app.core.logger import get_logger
from app.gui.theme import DARK_THEME
from app.memory.memory import MemoryManager

logger = get_logger(__name__)

try:
    from app.voice.piper import PiperTTSProvider
    from app.voice.tts import TTSResult
    from app.voice.whisper import FasterWhisperProvider
except Exception as exc:  # noqa: BLE001
    PiperTTSProvider = None  # type: ignore[misc,assignment]
    TTSResult = None  # type: ignore[misc,assignment]
    FasterWhisperProvider = None  # type: ignore[misc,assignment]
    logger.debug(f"Voice dependencies unavailable: {exc}")


class MessageWidget(QFrame):
    """Chat message widget."""

    def __init__(self, text: str, is_user: bool, timestamp: datetime | None = None) -> None:
        super().__init__()
        self.setObjectName("userMessage" if is_user else "assistantMessage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self._text_label = QLabel(text)
        self._text_label.setObjectName("messageText")
        self._text_label.setWordWrap(True)
        self._text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._text_label)

        if timestamp is None:
            timestamp = datetime.now(tz=datetime.now().astimezone().tzinfo)
        time_str = timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setObjectName("messageTime")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(time_label)


class ChatWorker(QObject):
    """Worker for async chat processing."""

    finished = Signal(str)
    error = Signal(str)
    thinking = Signal(bool)

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def run(self) -> None:
        try:
            self.thinking.emit(True)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from app.ai.agent import MartinAgent
            from app.ai.ollama import OllamaProvider
            provider = OllamaProvider()
            agent = MartinAgent(provider)
            response = loop.run_until_complete(agent.chat(self._message))
            loop.close()
            self.finished.emit(response)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Chat error: {e}")
            self.error.emit(str(e))
        finally:
            self.thinking.emit(False)


class TTSWorker(QObject):
    """Worker for non-blocking TTS playback."""

    finished = Signal()

    def __init__(self, text: str) -> None:
        super().__init__()
        self._text = text

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            provider = PiperTTSProvider()
            available = loop.run_until_complete(provider.is_available())
            if not available:
                return
            synth_result: TTSResult = loop.run_until_complete(provider.synthesize(self._text))
            if synth_result.success and synth_result.audio_data:
                loop.run_until_complete(provider.play_audio(synth_result.audio_data, synth_result.sample_rate))
            loop.close()
        except Exception as e:  # noqa: BLE001
            logger.debug(f"TTS playback skipped: {e}")
        finally:
            self.finished.emit()


class STTWorker(QObject):
    """Worker for speech-to-text transcription."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, audio_data: bytes, sample_rate: int) -> None:
        super().__init__()
        self._audio_data = audio_data
        self._sample_rate = sample_rate

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            provider = FasterWhisperProvider()
            result = loop.run_until_complete(provider.transcribe(self._audio_data, self._sample_rate))
            loop.close()
            self.finished.emit(result.text)
        except Exception as e:  # noqa: BLE001
            logger.error(f"STT error: {e}")
            self.error.emit(str(e))


class ChatPage(QWidget):
    """Chat page for interacting with Martin."""

    def __init__(self) -> None:
        super().__init__()
        self._agent: MartinAgent | None = None
        self._memory = MemoryManager()
        self._worker_thread: QThread | None = None
        self._worker: ChatWorker | None = None
        self._tts_enabled = True
        self._tts_thread: QThread | None = None
        self._tts_worker: TTSWorker | None = None
        self._stt_provider = FasterWhisperProvider() if FasterWhisperProvider is not None else None
        self._is_recording = False
        self._record_thread: QThread | None = None
        self._stt_worker: STTWorker | None = None
        self._init_ui()
        self._init_agent()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        title = QLabel("Chat")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 6}pt; font-weight: bold; color: {DARK_THEME.text_primary}; letter-spacing: 1px;")
        main_layout.addWidget(title)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"background-color: {DARK_THEME.background}; border: none;")

        self._chat_widget = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_widget)
        self._chat_layout.setContentsMargins(4, 4, 4, 4)
        self._chat_layout.setSpacing(10)
        self._chat_layout.addStretch()

        self._scroll_area.setWidget(self._chat_widget)
        main_layout.addWidget(self._scroll_area, 1)

        status_layout = QHBoxLayout()
        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("secondaryLabel")
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()

        self._mic_button = QPushButton("🎤")
        self._mic_button.setObjectName("secondaryButton")
        self._mic_button.setToolTip("Hold to talk")
        self._mic_button.setFixedHeight(38)
        self._mic_button.setFixedWidth(42)
        self._mic_button.setEnabled(FasterWhisperProvider is not None)
        self._mic_button.pressed.connect(self._start_recording)
        self._mic_button.released.connect(self._stop_recording)
        status_layout.addWidget(self._mic_button)

        self._tts_button = QPushButton("TTS")
        self._tts_button.setObjectName("secondaryButton")
        self._tts_button.setCheckable(True)
        self._tts_button.setChecked(True)
        self._tts_button.setToolTip("Toggle text-to-speech")
        self._tts_button.clicked.connect(self._toggle_tts)
        self._tts_button.setEnabled(PiperTTSProvider is not None)
        status_layout.addWidget(self._tts_button)

        main_layout.addLayout(status_layout)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("Type a message...")
        self._input_field.returnPressed.connect(self._send_message)
        self._input_field.setMinimumHeight(44)
        input_layout.addWidget(self._input_field, 1)

        self._send_button = QPushButton("Send")
        self._send_button.setMinimumHeight(44)
        self._send_button.setMinimumWidth(110)
        self._send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_button)

        self._stop_button = QPushButton("Stop")
        self._stop_button.setObjectName("secondaryButton")
        self._stop_button.setMinimumHeight(44)
        self._stop_button.setMinimumWidth(90)
        self._stop_button.setVisible(False)
        self._stop_button.clicked.connect(self._stop_generation)
        input_layout.addWidget(self._stop_button)

        main_layout.addLayout(input_layout)

        self._add_message("Ahoj! Jak ti mohu dnes pomoci?", is_user=False)

    def _init_agent(self) -> None:
        try:
            provider = OllamaProvider()
            self._agent = MartinAgent(provider)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to initialize agent: {e}")
            self._add_message(f"Error initializing AI: {e}", is_user=False)
            self._input_field.setEnabled(False)
            self._send_button.setEnabled(False)

    @Slot()
    def _send_message(self) -> None:
        text = self._input_field.text().strip()
        if not text or not self._agent:
            return

        if text.lower() in ("konec", "exit", "quit"):
            self._add_message("Na shledanou!", is_user=False)
            return

        if text.lower() == "pam�":
            memories = self._memory.get_long_term(limit=10)
            if memories:
                msg = "\n--- Dlouhodob� pam� ---\n" + "\n".join(f"  [{m['category']}] {m['content']}" for m in memories)
            else:
                msg = "Pam� je pr�zdn�."
            self._add_message(msg, is_user=False)
            return

        if text.lower() == "zapome�":
            self._memory.clear_short_term()
            self._add_message("Historie vymaz�na.", is_user=False)
            return

        if text.lower().startswith("zapamatuj si "):
            content = text[13:].strip()
            if content:
                self._memory.add_long_term(content, category="user", importance=5)
                self._add_message(f"Zapamatoval jsem si: {content}", is_user=False)
            else:
                self._add_message("Co m�m zapamatovat?", is_user=False)
            return

        self._add_message(text, is_user=True)
        self._input_field.clear()
        self._set_generating(True)

        self._worker_thread = QThread()
        self._worker = ChatWorker(text)
        self._worker.moveToThread(self._worker_thread)

        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.thinking.connect(self._on_thinking)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    def _process_voice_text(self, text: str) -> None:
        if not text.strip() or not self._agent:
            return
        if text.lower() in ("konec", "exit", "quit"):
            self._add_message("Na shledanou!", is_user=False)
            return
        self._add_message(text, is_user=True)
        self._set_generating(True)

        self._worker_thread = QThread()
        self._worker = ChatWorker(text)
        self._worker.moveToThread(self._worker_thread)

        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.thinking.connect(self._on_thinking)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    @Slot(str)
    def _on_response(self, response: str) -> None:
        self._add_message(response, is_user=False)
        self._set_generating(False)
        if self._tts_enabled:
            self._play_tts(response)

    @Slot(str)
    def _on_error(self, error: str) -> None:
        self._add_message(f"Chyba: {error}", is_user=False)
        self._set_generating(False)

    @Slot(bool)
    def _on_thinking(self, thinking: bool) -> None:
        if thinking:
            self._status_label.setText("Martin p�em��l�...")
        else:
            self._status_label.setText("Ready")

    def _set_generating(self, generating: bool) -> None:
        self._input_field.setEnabled(not generating)
        self._send_button.setVisible(not generating)
        self._stop_button.setVisible(generating)
        if generating:
            self._status_label.setText("Martin p�em��l�...")

    @Slot()
    def _stop_generation(self) -> None:
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.terminate()
            self._worker_thread.wait(1000)
        self._set_generating(False)
        self._status_label.setText("Stopped")

    @Slot()
    def _toggle_tts(self) -> None:
        self._tts_enabled = self._tts_button.isChecked()
        self._tts_button.setText("🎤 TTS On" if self._tts_enabled else "🎤 TTS Off")

    def _play_tts(self, text: str) -> None:
        if PiperTTSProvider is None or not text.strip():
            return
        self._tts_thread = QThread()
        self._tts_worker = TTSWorker(text)
        self._tts_worker.moveToThread(self._tts_thread)
        self._tts_worker.finished.connect(self._tts_thread.quit)
        self._tts_worker.finished.connect(self._tts_worker.deleteLater)
        self._tts_thread.finished.connect(self._tts_thread.deleteLater)
        self._tts_thread.started.connect(self._tts_worker.run)
        self._tts_thread.start()

    @Slot()
    def _start_recording(self) -> None:
        if not self._agent or self._is_recording or FasterWhisperProvider is None:
            return
        self._is_recording = True
        self._mic_button.setText("🎤")
        self._status_label.setText("Listening...")

        def record_audio():
            try:
                duration = 10
                sample_rate = 16000
                channels = 1
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype="int16")
                sd.wait()
                audio_data = recording.tobytes()
                self._stt_worker = STTWorker(audio_data, sample_rate)
                self._record_thread = QThread()
                self._stt_worker.moveToThread(self._record_thread)
                self._stt_worker.finished.connect(self._on_stt_result)
                self._stt_worker.error.connect(self._on_stt_error)
                self._record_thread.started.connect(self._stt_worker.run)
                self._stt_worker.finished.connect(self._record_thread.quit)
                self._stt_worker.finished.connect(self._stt_worker.deleteLater)
                self._record_thread.finished.connect(self._record_thread.deleteLater)
                self._record_thread.start()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Recording error: {e}")
                self._is_recording = False
                self._mic_button.setText("🎤")
                self._status_label.setText("Ready")

        threading.Thread(target=record_audio, daemon=True).start()

    @Slot()
    def _stop_recording(self) -> None:
        self._mic_button.setText("🎤")
        if not self._is_recording:
            return
        self._is_recording = False
        sd.stop()
        self._status_label.setText("Transcribing...")

    @Slot(str)
    def _on_stt_result(self, text: str) -> None:
        self._is_recording = False
        self._mic_button.setText("🎤")
        self._status_label.setText("Ready")
        if not text.strip():
            return
        self._process_voice_text(text)

    @Slot(str)
    def _on_stt_error(self, error: str) -> None:
        self._is_recording = False
        self._mic_button.setText("🎤")
        self._status_label.setText(f"STT Error: {error}")

    def _add_message(self, text: str, is_user: bool) -> None:
        msg = MessageWidget(text, is_user)
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, msg)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self) -> None:
        self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        )

