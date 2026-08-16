"""
Tools page for Martin GUI.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.logger import get_logger
from app.core.tools import SafetyLevel, get_tool_registry
from app.gui.theme import DARK_THEME

logger = get_logger(__name__)


class ToolItemWidget(QFrame):
    """Tool list item widget."""

    toggled = Signal(str, bool)

    def __init__(self, tool) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._tool = tool

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Tool info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_layout = QHBoxLayout()
        name_label = QLabel(tool.name)
        name_label.setStyleSheet(f"font-weight: bold; font-size: {DARK_THEME.font_size}pt;")
        name_layout.addWidget(name_label)

        # Safety badge
        safety_label = QLabel(tool.safety_level.value.upper())
        safety_label.setFixedWidth(80)
        safety_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        safety_label.setStyleSheet(self._get_safety_style(tool.safety_level))
        name_layout.addWidget(safety_label)

        name_layout.addStretch()
        info_layout.addLayout(name_layout)

        desc_label = QLabel(tool.description)
        desc_label.setObjectName("secondaryLabel")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout, 1)

        # Enable checkbox
        self._checkbox = QCheckBox("Enabled")
        self._checkbox.setChecked(get_tool_registry().is_enabled(tool.name))
        self._checkbox.toggled.connect(lambda checked: self.toggled.emit(tool.name, checked))
        layout.addWidget(self._checkbox)

    def _get_safety_style(self, level: SafetyLevel) -> str:
        """Get style for safety level badge."""
        colors = {
            SafetyLevel.SAFE: ("#107c10", "#dff6dd"),
            SafetyLevel.CAUTION: ("#bf8700", "#fff3cd"),
            SafetyLevel.DANGEROUS: ("#d13438", "#f8d7da"),
        }
        bg, text = colors.get(level, ("#666666", "#ffffff"))
        return f"""
            background-color: {bg};
            color: {text};
            border-radius: 4px;
            padding: 2px 8px;
            font-size: {DARK_THEME.font_size_small}pt;
            font-weight: bold;
        """


class ToolsPage(QWidget):
    """Tools page showing available tools."""

    def __init__(self) -> None:
        super().__init__()
        self._registry = get_tool_registry()
        self._init_ui()
        self._load_tools()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("Tools")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 4}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(title)

        # Description
        desc = QLabel("Manage available tools for Martin. Dangerous tools require explicit confirmation before execution.")
        desc.setObjectName("secondaryLabel")
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Tool list
        self._list = QListWidget()
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSpacing(8)
        main_layout.addWidget(self._list, 1)

    def _load_tools(self) -> None:
        """Load tools into list."""
        self._list.clear()
        tools = self._registry.list_tools()

        for tool in tools:
            item = QListWidgetItem()
            widget = ToolItemWidget(tool)
            widget.toggled.connect(self._on_tool_toggled)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)

    @Slot(str, bool)
    def _on_tool_toggled(self, tool_name: str, enabled: bool) -> None:
        """Handle tool enable/disable."""
        if enabled:
            self._registry.enable(tool_name)
        else:
            self._registry.disable(tool_name)
        logger.info(f"Tool '{tool_name}' {'enabled' if enabled else 'disabled'}")