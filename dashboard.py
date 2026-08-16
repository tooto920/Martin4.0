"""
Dashboard page for Martin GUI.
"""
import asyncio

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ai.ollama import OllamaProvider
from app.computer.monitor import get_resource_monitor
from app.core.config import get_config
from app.core.events import get_event_bus
from app.core.logger import get_logger
from app.gui.theme import DARK_THEME
from app.integrations.msfs import get_msfs_integration
from app.memory.memory import MemoryManager

logger = get_logger(__name__)


class MetricCard(QFrame):
    """Metric display card."""

    def __init__(self, title: str, value: str = "", unit: str = "", subtitle: str = "") -> None:
        super().__init__()
        self.setObjectName("panel")
        self.setFixedHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("secondaryLabel")
        layout.addWidget(self._title_label)

        value_layout = QHBoxLayout()
        value_layout.setSpacing(6)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("valueLabel")
        value_layout.addWidget(self._value_label)

        if unit:
            self._unit_label = QLabel(unit)
            self._unit_label.setObjectName("secondaryLabel")
            value_layout.addWidget(self._unit_label)

        value_layout.addStretch()
        layout.addLayout(value_layout)

    def update_value(self, value: str, subtitle: str = "") -> None:
        self._value_label.setText(value)


class DashboardPage(QWidget):
    """Dashboard page showing system overview."""

    def __init__(self) -> None:
        super().__init__()
        self._config = get_config()
        self._resource_monitor = get_resource_monitor()
        self._event_bus = get_event_bus()
        self._memory = MemoryManager()
        self._ollama_provider = OllamaProvider()
        self._msfs = get_msfs_integration()
        self._ollama_available = False
        self._init_ui()
        self._start_updates()
        self._event_bus.subscribe("msfs_connected", self._on_msfs_connected)
        self._event_bus.subscribe("msfs_disconnected", self._on_msfs_disconnected)
        self._event_bus.subscribe("msfs_data_updated", self._on_msfs_data_updated)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 6}pt; font-weight: bold; color: {DARK_THEME.text_primary}; letter-spacing: 1px;")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background-color: {DARK_THEME.background}; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        # AI Status row
        ai_row = QHBoxLayout()
        ai_row.setSpacing(18)

        self._model_card = MetricCard("AI Model", "Loading...")
        self._ollama_status_card = MetricCard("Ollama", "Checking...")
        self._mode_card = MetricCard("Mode", "Loading...")
        ai_row.addWidget(self._model_card)
        ai_row.addWidget(self._ollama_status_card)
        ai_row.addWidget(self._mode_card)
        content_layout.addLayout(ai_row)

        # System Resources
        resources_grid = QGridLayout()
        resources_grid.setSpacing(18)

        self._cpu_card = MetricCard("CPU", "-", "%")
        self._ram_card = MetricCard("RAM", "-", "GB", "Used / Total")
        self._gpu_card = MetricCard("GPU", "-", "%")
        self._vram_card = MetricCard("VRAM", "-", "MB", "Used / Total")

        resources_grid.addWidget(self._cpu_card, 0, 0)
        resources_grid.addWidget(self._ram_card, 0, 1)
        resources_grid.addWidget(self._gpu_card, 1, 0)
        resources_grid.addWidget(self._vram_card, 1, 1)

        content_layout.addLayout(resources_grid)

        # Memory
        memory_row = QHBoxLayout()
        memory_row.setSpacing(18)

        self._memory_card = MetricCard("Long-term Memories", "-", "items")
        self._context_card = MetricCard("Context", "-", "tokens")

        memory_row.addWidget(self._memory_card)
        memory_row.addWidget(self._context_card)
        content_layout.addLayout(memory_row)

        # Flight Mode
        flight_title = QLabel("Flight")
        flight_title.setStyleSheet(f"font-size: {DARK_THEME.font_size + 2}pt; font-weight: bold; color: {DARK_THEME.text_primary}; letter-spacing: 1px;")
        content_layout.addWidget(flight_title)

        flight_row = QHBoxLayout()
        flight_row.setSpacing(18)

        self._flight_status_card = MetricCard("Status", "Not connected")
        self._aircraft_card = MetricCard("Aircraft", "-")

        flight_row.addWidget(self._flight_status_card)
        flight_row.addWidget(self._aircraft_card)
        content_layout.addLayout(flight_row)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        self._update_ai_info()

    def _start_updates(self) -> None:
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_resources)
        self._timer.timeout.connect(self._update_memory_info)
        self._timer.timeout.connect(self._check_ollama)
        self._timer.timeout.connect(self._update_msfs_summary)
        self._timer.start(2000)

    @Slot()
    def _update_resources(self) -> None:
        resources = self._resource_monitor.latest
        if resources:
            self._cpu_card.update_value(f"{resources.cpu_percent:.0f}")
            ram_used = f"{resources.ram_used_gb:.1f}"
            ram_total = f"{resources.ram_total_gb:.1f}"
            self._ram_card.update_value(f"{ram_used} / {ram_total}")
            if resources.gpu_available and resources.gpu_percent is not None:
                self._gpu_card.update_value(f"{resources.gpu_percent:.0f}")
                if resources.gpu_used_mb and resources.gpu_total_mb:
                    self._vram_card.update_value(f"{resources.gpu_used_mb:.0f} / {resources.gpu_total_mb:.0f}")
            else:
                self._gpu_card.update_value("Unavailable")
                self._vram_card.update_value("Unavailable")

    @Slot()
    def _update_memory_info(self) -> None:
        try:
            count = len(self._memory.get_long_term(limit=1000))
            self._memory_card.update_value(str(count), "items")
        except Exception:  # noqa: BLE001
            self._memory_card.update_value("0", "No memories stored")
        self._context_card.update_value("N/A", "Not exposed by Ollama")

    @Slot()
    def _check_ollama(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            available = loop.run_until_complete(self._ollama_provider.is_available())
            loop.close()
            self._ollama_available = available
            if available:
                self._ollama_status_card.update_value("Running")
                self._ollama_status_card.setStyleSheet(f"background-color: {DARK_THEME.panel}; border: 1px solid {DARK_THEME.border}; border-radius: 8px;")
            else:
                self._ollama_status_card.update_value("Unavailable")
        except Exception:  # noqa: BLE001
            self._ollama_status_card.update_value("Error")

    def _update_ai_info(self) -> None:
        model = self._config.get("ai", "model", default="gemma3:4b")
        mode = self._config.get("modes", "active", default="general")
        self._model_card.update_value(model)
        self._mode_card.update_value(mode.capitalize())

    def _on_msfs_connected(self) -> None:
        self._flight_status_card.update_value("Connected")
        self._update_msfs_summary()

    def _on_msfs_disconnected(self) -> None:
        self._flight_status_card.update_value("MSFS not connected")
        self._aircraft_card.update_value("�")

    def _on_msfs_data_updated(self, aircraft, flight) -> None:
        self._aircraft_card.update_value(aircraft.name)

    def _update_msfs_summary(self) -> None:
        if self._msfs.is_connected:
            self._flight_status_card.update_value("Connected")
            self._aircraft_card.update_value(self._msfs.aircraft.name)
        else:
            self._flight_status_card.update_value("MSFS not connected")
            self._aircraft_card.update_value("�")

