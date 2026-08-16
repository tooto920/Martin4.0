"""
Flight Mode page for Martin GUI.
"""
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.config import get_config
from app.gui.theme import DARK_THEME


class FlightMetricCard(QFrame):
    """Flight metric display card."""

    def __init__(self, title: str, value: str = "—", unit: str = "") -> None:
        super().__init__()
        self.setObjectName("panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("secondaryLabel")
        layout.addWidget(self._title_label)

        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("valueLabel")
        value_layout.addWidget(self._value_label)

        if unit:
            self._unit_label = QLabel(unit)
            self._unit_label.setObjectName("secondaryLabel")
            value_layout.addWidget(self._unit_label)

        value_layout.addStretch()
        layout.addLayout(value_layout)

    def update_value(self, value: str, unit: str = "") -> None:
        """Update displayed value."""
        self._value_label.setText(value)
        if unit and hasattr(self, "_unit_label"):
            self._unit_label.setText(unit)


class FlightPage(QWidget):
    """Flight Mode page for MSFS integration."""

    def __init__(self) -> None:
        super().__init__()
        self._config = get_config()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("Flight Mode")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 4}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(title)

        # Connection status
        status_layout = QHBoxLayout()
        self._status_label = QLabel("MSFS: Not connected")
        self._status_label.setStyleSheet(f"color: {DARK_THEME.warning}; font-weight: bold;")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._connect_btn = QPushButton("Connect to MSFS")
        self._connect_btn.setObjectName("secondaryButton")
        self._connect_btn.setEnabled(False)  # Disabled until SimConnect implemented
        self._connect_btn.setToolTip("SimConnect integration coming in future phase")
        status_layout.addWidget(self._connect_btn)

        main_layout.addLayout(status_layout)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # Aircraft info
        aircraft_title = QLabel("Aircraft Information")
        aircraft_title.setStyleSheet(f"font-size: {DARK_THEME.font_size + 2}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(aircraft_title)

        aircraft_grid = QGridLayout()
        aircraft_grid.setSpacing(16)

        self._aircraft_card = FlightMetricCard("Aircraft", "—")
        self._altitude_card = FlightMetricCard("Altitude", "—", "ft")
        self._speed_card = FlightMetricCard("Speed", "—", "kts")
        self._heading_card = FlightMetricCard("Heading", "—", "°")

        aircraft_grid.addWidget(self._aircraft_card, 0, 0)
        aircraft_grid.addWidget(self._altitude_card, 0, 1)
        aircraft_grid.addWidget(self._speed_card, 1, 0)
        aircraft_grid.addWidget(self._heading_card, 1, 1)

        main_layout.addLayout(aircraft_grid)

        # Flight parameters
        params_title = QLabel("Flight Parameters")
        params_title.setStyleSheet(f"font-size: {DARK_THEME.font_size + 2}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(params_title)

        params_grid = QGridLayout()
        params_grid.setSpacing(16)

        self._vs_card = FlightMetricCard("Vertical Speed", "—", "ft/min")
        self._fuel_card = FlightMetricCard("Fuel", "—", "lbs")
        self._autopilot_card = FlightMetricCard("Autopilot", "—")
        self._gear_card = FlightMetricCard("Gear", "—")
        self._flaps_card = FlightMetricCard("Flaps", "—")

        params_grid.addWidget(self._vs_card, 0, 0)
        params_grid.addWidget(self._fuel_card, 0, 1)
        params_grid.addWidget(self._autopilot_card, 1, 0)
        params_grid.addWidget(self._gear_card, 1, 1)
        params_grid.addWidget(self._flaps_card, 2, 0)

        main_layout.addLayout(params_grid)

        # Navigation
        nav_title = QLabel("Navigation")
        nav_title.setStyleSheet(f"font-size: {DARK_THEME.font_size + 2}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(nav_title)

        nav_grid = QGridLayout()
        nav_grid.setSpacing(16)

        self._position_card = FlightMetricCard("Position", "—")
        self._destination_card = FlightMetricCard("Destination", "—")
        self._status_card = FlightMetricCard("Flight Status", "—")
        self._eta_card = FlightMetricCard("ETA", "—")

        nav_grid.addWidget(self._position_card, 0, 0)
        nav_grid.addWidget(self._destination_card, 0, 1)
        nav_grid.addWidget(self._status_card, 1, 0)
        nav_grid.addWidget(self._eta_card, 1, 1)

        main_layout.addLayout(nav_grid)

        # Placeholder notice
        notice = QLabel(
            "⚠️ Flight Simulator integration not yet implemented.\n"
            "This UI is a foundation for future SimConnect integration.\n"
            "Real data will appear here when MSFS 2024 is connected."
        )
        notice.setObjectName("secondaryLabel")
        notice.setWordWrap(True)
        notice.setStyleSheet(f"padding: 16px; background-color: {DARK_THEME.panel}; border: 1px solid {DARK_THEME.warning}; border-radius: 8px;")
        main_layout.addWidget(notice)

        main_layout.addStretch()

    def set_connected(self, connected: bool) -> None:
        """Set connection status."""
        if connected:
            self._status_label.setText("MSFS: Connected")
            self._status_label.setStyleSheet(f"color: {DARK_THEME.success}; font-weight: bold;")
            self._connect_btn.setText("Disconnect")
        else:
            self._status_label.setText("MSFS: Not connected")
            self._status_label.setStyleSheet(f"color: {DARK_THEME.warning}; font-weight: bold;")
            self._connect_btn.setText("Connect to MSFS")

    def update_aircraft_data(self, data: dict) -> None:
        """Update aircraft data."""
        self._aircraft_card.update_value(data.get("aircraft", "—"))
        self._altitude_card.update_value(data.get("altitude", "—"), "ft")
        self._speed_card.update_value(data.get("speed", "—"), "kts")
        self._heading_card.update_value(data.get("heading", "—"), "°")
        self._vs_card.update_value(data.get("vertical_speed", "—"), "ft/min")
        self._fuel_card.update_value(data.get("fuel", "—"), "lbs")
        self._autopilot_card.update_value(data.get("autopilot", "—"))
        self._gear_card.update_value(data.get("gear", "—"))
        self._flaps_card.update_value(data.get("flaps", "—"))
        self._position_card.update_value(data.get("position", "—"))
        self._destination_card.update_value(data.get("destination", "—"))
        self._status_card.update_value(data.get("flight_status", "—"))
        self._eta_card.update_value(data.get("eta", "—"))