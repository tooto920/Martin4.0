"""
Settings page for Martin GUI.
"""
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config import get_config
from app.core.logger import get_logger
from app.gui.theme import DARK_THEME

logger = get_logger(__name__)


class SettingsPage(QWidget):
    """Settings page for Martin configuration."""

    def __init__(self) -> None:
        super().__init__()
        self._config = get_config()
        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 4}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(title)

        # Tab widget
        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs, 1)

        # AI Settings tab
        self._tabs.addTab(self._create_ai_tab(), "AI")

        # Voice Settings tab
        self._tabs.addTab(self._create_voice_tab(), "Voice")

        # GUI Settings tab
        self._tabs.addTab(self._create_gui_tab(), "Appearance")

        # Mode Settings tab
        self._tabs.addTab(self._create_mode_tab(), "Modes")

        # Advanced tab
        self._tabs.addTab(self._create_advanced_tab(), "Advanced")

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self._save_btn = QPushButton("Save Settings")
        self._save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(self._save_btn)
        main_layout.addLayout(save_layout)

    def _create_ai_tab(self) -> QWidget:
        """Create AI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Provider
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setSpacing(12)

        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("e.g., gemma3:4b")
        form.addRow("Model:", self._model_input)

        self._ollama_url_input = QLineEdit()
        self._ollama_url_input.setPlaceholderText("http://localhost:11434")
        form.addRow("Ollama URL:", self._ollama_url_input)

        self._temperature_spin = QDoubleSpinBox()
        self._temperature_spin.setRange(0.0, 2.0)
        self._temperature_spin.setSingleStep(0.1)
        self._temperature_spin.setDecimals(1)
        form.addRow("Temperature:", self._temperature_spin)

        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(100, 8192)
        self._max_tokens_spin.setSingleStep(256)
        form.addRow("Max Tokens:", self._max_tokens_spin)

        layout.addLayout(form)

        # System prompt
        layout.addWidget(QLabel("System Prompt:"))
        self._system_prompt = QLineEdit()
        self._system_prompt.setPlaceholderText("System prompt (loaded from config)")
        layout.addWidget(self._system_prompt)

        layout.addStretch()
        return widget

    def _create_voice_tab(self) -> QWidget:
        """Create voice settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # TTS
        tts_group = QGroupBox("Text-to-Speech")
        tts_layout = QFormLayout(tts_group)
        tts_layout.setSpacing(12)

        self._tts_enabled = QCheckBox("Enable TTS")
        tts_layout.addRow(self._tts_enabled)

        self._tts_provider = QComboBox()
        self._tts_provider.addItems(["piper"])
        tts_layout.addRow("Provider:", self._tts_provider)

        self._tts_voice = QComboBox()
        self._tts_voice.setPlaceholderText("Loading voices...")
        tts_layout.addRow("Voice:", self._tts_voice)

        self._tts_speed = QDoubleSpinBox()
        self._tts_speed.setRange(0.5, 2.0)
        self._tts_speed.setSingleStep(0.1)
        self._tts_speed.setDecimals(1)
        tts_layout.addRow("Speed:", self._tts_speed)

        layout.addWidget(tts_group)

        # STT
        stt_group = QGroupBox("Speech-to-Text")
        stt_layout = QFormLayout(stt_group)
        stt_layout.setSpacing(12)

        self._stt_enabled = QCheckBox("Enable STT")
        stt_layout.addRow(self._stt_enabled)

        self._stt_provider = QComboBox()
        self._stt_provider.addItems(["faster-whisper"])
        stt_layout.addRow("Provider:", self._stt_provider)

        self._stt_model = QComboBox()
        self._stt_model.addItems(["tiny", "base", "small", "medium", "large"])
        stt_layout.addRow("Model:", self._stt_model)

        self._stt_language = QComboBox()
        self._stt_language.addItems(["cs", "en", "auto"])
        stt_layout.addRow("Language:", self._stt_language)

        layout.addWidget(stt_group)

        layout.addStretch()
        return widget

    def _create_gui_tab(self) -> QWidget:
        """Create GUI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        form.addRow("Theme:", self._theme_combo)

        self._font_family = QLineEdit()
        form.addRow("Font Family:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 16)
        form.addRow("Font Size:", self._font_size)

        self._accent_color = QLineEdit()
        self._accent_color.setPlaceholderText("#0078d4")
        form.addRow("Accent Color:", self._accent_color)

        self._bg_color = QLineEdit()
        self._bg_color.setPlaceholderText("#1a1a2e")
        form.addRow("Background Color:", self._bg_color)

        self._panel_color = QLineEdit()
        self._panel_color.setPlaceholderText("#16213e")
        form.addRow("Panel Color:", self._panel_color)

        layout.addLayout(form)
        layout.addStretch()
        return widget

    def _create_mode_tab(self) -> QWidget:
        """Create mode settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Active mode
        form = QFormLayout()
        form.setSpacing(12)

        self._active_mode = QComboBox()
        self._active_mode.addItems(["general", "gaming", "flight", "coding", "study"])
        form.addRow("Active Mode:", self._active_mode)

        layout.addLayout(form)

        # Mode descriptions
        layout.addWidget(QLabel("Mode Descriptions:"))
        self._mode_descriptions = QLineEdit()
        self._mode_descriptions.setPlaceholderText("Mode-specific prompts (loaded from config)")
        layout.addWidget(self._mode_descriptions)

        layout.addStretch()
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(12)

        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("Log Level:", self._log_level)

        self._log_file = QLineEdit()
        log_layout.addRow("Log File:", self._log_file)

        layout.addWidget(log_group)

        # Resource monitor
        monitor_group = QGroupBox("Resource Monitor")
        monitor_layout = QFormLayout(monitor_group)
        monitor_layout.setSpacing(12)

        self._monitor_interval = QDoubleSpinBox()
        self._monitor_interval.setRange(0.5, 10.0)
        self._monitor_interval.setSingleStep(0.5)
        self._monitor_interval.setDecimals(1)
        self._monitor_interval.setSuffix(" sec")
        monitor_layout.addRow("Update Interval:", self._monitor_interval)

        self._enable_gpu = QCheckBox("Enable GPU Monitoring")
        monitor_layout.addRow(self._enable_gpu)

        layout.addWidget(monitor_group)

        # Security
        security_group = QGroupBox("Security")
        security_layout = QVBoxLayout(security_group)

        self._confirm_dangerous = QCheckBox("Require confirmation for dangerous tools")
        security_layout.addWidget(self._confirm_dangerous)

        self._allow_shell = QCheckBox("Allow shell execution (DANGEROUS)")
        security_layout.addWidget(self._allow_shell)

        layout.addWidget(security_group)

        layout.addStretch()
        return widget

    def _load_settings(self) -> None:
        """Load settings from config."""
        # AI
        self._model_input.setText(self._config.get("ai", "model", default="gemma3:4b"))
        self._ollama_url_input.setText(self._config.get("ai", "ollama_url", default="http://localhost:11434"))
        self._temperature_spin.setValue(self._config.get("ai", "temperature", default=0.7))
        self._max_tokens_spin.setValue(self._config.get("ai", "max_tokens", default=2048))

        # Voice
        self._tts_enabled.setChecked(self._config.get("voice", "tts", "enabled", default=True))
        self._tts_voice.setCurrentText(self._config.get("voice", "tts", "voice", default="cs_CZ-jirka-medium"))
        self._tts_speed.setValue(self._config.get("voice", "tts", "speed", default=1.0))

        self._stt_enabled.setChecked(self._config.get("voice", "stt", "enabled", default=False))
        self._stt_model.setCurrentText(self._config.get("voice", "stt", "model", default="base"))
        self._stt_language.setCurrentText(self._config.get("voice", "stt", "language", default="cs"))

        # GUI
        self._theme_combo.setCurrentText(self._config.get("gui", "theme", default="Dark"))
        self._font_family.setText(self._config.get("gui", "font_family", default="Segoe UI"))
        self._font_size.setValue(self._config.get("gui", "font_size", default=10))
        self._accent_color.setText(self._config.get("gui", "accent_color", default="#0078d4"))
        self._bg_color.setText(self._config.get("gui", "background_color", default="#1a1a2e"))
        self._panel_color.setText(self._config.get("gui", "panel_color", default="#16213e"))

        # Mode
        self._active_mode.setCurrentText(self._config.get("modes", "active", default="general"))

        # Advanced
        self._log_level.setCurrentText(self._config.get("logging", "level", default="INFO"))
        self._log_file.setText(self._config.get("logging", "file", default="data/logs/martin.log"))
        self._monitor_interval.setValue(self._config.get("monitor", "update_interval_sec", default=1.0))
        self._enable_gpu.setChecked(self._config.get("monitor", "enable_gpu", default=True))
        self._confirm_dangerous.setChecked(self._config.get("tools", "dangerous_tools_require_confirmation", default=True))
        self._allow_shell.setChecked(self._config.get("security", "allow_shell_execution", default=False))

        # Load voices for TTS
        self._load_tts_voices()

    def _load_tts_voices(self) -> None:
        """Load available TTS voices."""
        # This would be async in real implementation
        # For now, just add the known voice
        self._tts_voice.addItem("cs_CZ-jirka-medium")

    @Slot()
    def _save_settings(self) -> None:
        """Save settings to config."""
        # Note: Current config implementation is read-only from file
        # This would need a config writer implementation
        QMessageBox.information(
            self, "Settings",
            "Settings saved (in-memory only).\n"
            "To persist, edit config/config.yaml directly.\n"
            "A config writer will be added in a future update."
        )
        logger.info("Settings save requested (read-only config)")