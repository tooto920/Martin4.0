"""
Main window for Martin GUI application.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config import get_config
from app.core.events import get_event_bus
from app.core.logger import get_logger
from app.gui.theme import DARK_THEME, Theme, get_stylesheet

logger = get_logger(__name__)


class SidebarButton(QPushButton):
    """Sidebar navigation button."""

    def __init__(self, text: str, icon: str = "", page_id: str = "") -> None:
        super().__init__()
        self.page_id = page_id
        self.setText(f"  {text}" if icon else text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_active(self, active: bool) -> None:
        """Set active state."""
        self.setChecked(active)
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """Sidebar navigation widget."""

    page_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._buttons: dict[str, SidebarButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("MARTIN")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Navigation buttons
        nav_items = [
            ("Dashboard", "📊", "dashboard"),
            ("Chat", "💬", "chat"),
            ("Tools", "🔧", "tools"),
            ("Memory", "🧠", "memory"),
            ("Knowledge", "📚", "knowledge"),
            ("Flight Mode", "✈️", "flight"),
            ("Settings", "⚙️", "settings"),
        ]

        for text, icon, page_id in nav_items:
            btn = SidebarButton(text, icon, page_id)
            btn.clicked.connect(lambda checked, pid=page_id: self._on_button_clicked(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Version label
        config = get_config()
        version = config.get("app", "version", default="1.0.0")
        version_label = QLabel(f"v{version}")
        version_label.setObjectName("secondaryLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFixedHeight(30)
        layout.addWidget(version_label)

        # Set default active
        self._set_active("dashboard")

    def _on_button_clicked(self, page_id: str) -> None:
        """Handle button click."""
        self._set_active(page_id)
        self.page_changed.emit(page_id)

    def _set_active(self, page_id: str) -> None:
        """Set active button."""
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Martin - Local AI Assistant")
        self._config = get_config()
        self._event_bus = get_event_bus()
        self._pages: dict[str, QWidget] = {}
        self._current_page = "dashboard"

        self._setup_ui()
        self._apply_theme()
        self._load_window_state()

        # Connect to resource monitor events
        self._event_bus.subscribe("resources_updated", self._on_resources_updated)

    def _setup_ui(self) -> None:
        """Setup main UI."""
        # Central widget
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)
        main_layout.addWidget(self._sidebar)

        # Content area
        self._content_area = QWidget()
        self._content_area.setObjectName("contentArea")
        content_layout = QVBoxLayout(self._content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for pages
        self._stacked_widget = QStackedWidget()
        content_layout.addWidget(self._stacked_widget)

        main_layout.addWidget(self._content_area, 1)

        # Initialize pages
        self._init_pages()

    def _init_pages(self) -> None:
        """Initialize all pages."""
        from app.gui.pages.chat import ChatPage
        from app.gui.pages.dashboard import DashboardPage
        from app.gui.pages.flight import FlightPage
        from app.gui.pages.knowledge import KnowledgePage
        from app.gui.pages.memory import MemoryPage
        from app.gui.pages.settings import SettingsPage
        from app.gui.pages.tools import ToolsPage

        pages = {
            "dashboard": DashboardPage(),
            "chat": ChatPage(),
            "tools": ToolsPage(),
            "memory": MemoryPage(),
            "knowledge": KnowledgePage(),
            "flight": FlightPage(),
            "settings": SettingsPage(),
        }

        for page_id, page in pages.items():
            self._pages[page_id] = page
            self._stacked_widget.addWidget(page)

    def _switch_page(self, page_id: str) -> None:
        """Switch to page."""
        if page_id in self._pages:
            self._stacked_widget.setCurrentWidget(self._pages[page_id])
            self._current_page = page_id
            logger.debug(f"Switched to page: {page_id}")

    def _apply_theme(self) -> None:
        """Apply theme stylesheet."""
        theme = DARK_THEME
        # Override with config values
        gui_config = self._config.get_section("gui")
        if gui_config:
            theme = Theme(
                background=gui_config.get("background_color", theme.background),
                panel=gui_config.get("panel_color", theme.panel),
                border=gui_config.get("border_color", theme.border),
                accent=gui_config.get("accent_color", theme.accent),
                font_family=gui_config.get("font_family", theme.font_family),
                font_size=gui_config.get("font_size", theme.font_size),
            )

        self.setStyleSheet(get_stylesheet(theme))

    def _load_window_state(self) -> None:
        """Load window size and position from config."""
        gui_config = self._config.get_section("gui")
        width = gui_config.get("window_width", 1200)
        height = gui_config.get("window_height", 800)
        self.resize(width, height)
        self.setMinimumSize(900, 600)

    def _on_resources_updated(self, resources) -> None:
        """Handle resource update event."""
        # Forward to dashboard page if it's the current page
        if self._current_page == "dashboard" and hasattr(self._pages.get("dashboard"), "update_resources"):
            self._pages["dashboard"].update_resources(resources)  # type: ignore[attr-defined]

    def closeEvent(self, event) -> None:
        """Handle window close."""
        # Save window state (config is read-only in current implementation)
        event.accept()