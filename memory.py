"""
Memory page for Martin GUI.
"""
from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.logger import get_logger
from app.gui.theme import DARK_THEME
from app.memory.memory import MemoryManager

logger = get_logger(__name__)


class MemoryItemWidget(QFrame):
    """Memory list item widget."""

    delete_requested = Signal(int)

    def __init__(self, memory: dict) -> None:
        super().__init__()
        self.setObjectName("panel")
        self._memory_id = memory["id"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Memory info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Header with category and importance
        header_layout = QHBoxLayout()
        cat_label = QLabel(f"[{memory.get('category', 'general')}]")
        cat_label.setStyleSheet(f"color: {DARK_THEME.accent}; font-weight: bold;")
        header_layout.addWidget(cat_label)

        imp = memory.get("importance", 1)
        imp_label = QLabel(f"Importance: {imp}")
        imp_label.setObjectName("secondaryLabel")
        header_layout.addWidget(imp_label)

        # Date
        created = memory.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
                date_label = QLabel(date_str)
                date_label.setObjectName("secondaryLabel")
                header_layout.addWidget(date_label)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to parse memory date: {e}")

        header_layout.addStretch()
        info_layout.addLayout(header_layout)

        # Content
        content_label = QLabel(memory.get("content", ""))
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addWidget(content_label)

        layout.addLayout(info_layout, 1)

        # Delete button
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setObjectName("secondaryButton")
        self._delete_btn.setFixedWidth(80)
        self._delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self._delete_btn)

    def _on_delete(self) -> None:
        """Handle delete click."""
        self.delete_requested.emit(self._memory_id)


class MemoryPage(QWidget):
    """Memory page for viewing and managing memories."""

    def __init__(self) -> None:
        super().__init__()
        self._memory = MemoryManager()
        self._init_ui()
        self._load_memories()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Title bar
        title_layout = QHBoxLayout()
        title = QLabel("Memory")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 4}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        title_layout.addWidget(title)

        title_layout.addStretch()

        # Add memory button
        self._add_btn = QPushButton("Add Memory")
        self._add_btn.clicked.connect(self._add_memory)
        title_layout.addWidget(self._add_btn)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search memories...")
        self._search.setFixedWidth(250)
        self._search.textChanged.connect(self._filter_memories)
        title_layout.addWidget(self._search)

        main_layout.addLayout(title_layout)

        # Memory list
        self._list = QListWidget()
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSpacing(8)
        main_layout.addWidget(self._list, 1)

        # Stats
        self._stats_label = QLabel("0 memories")
        self._stats_label.setObjectName("secondaryLabel")
        main_layout.addWidget(self._stats_label)

    def _load_memories(self) -> None:
        """Load memories into list."""
        self._list.clear()
        memories = self._memory.get_long_term(limit=100)

        for memory in memories:
            self._add_memory_item(memory)

        self._stats_label.setText(f"{len(memories)} memories")

    def _add_memory_item(self, memory: dict) -> None:
        """Add memory item to list."""
        item = QListWidgetItem()
        widget = MemoryItemWidget(memory)
        widget.delete_requested.connect(self._delete_memory)
        item.setSizeHint(widget.sizeHint())
        self._list.addItem(item)
        self._list.setItemWidget(item, widget)

    @Slot()
    def _add_memory(self) -> None:
        """Add new memory."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Add Memory", "Enter memory content:",
            ""
        )
        if ok and text.strip():
            category, ok = QInputDialog.getItem(
                self, "Category", "Select category:",
                ["general", "user", "facts", "preferences", "technical"],
                0, False
            )
            if ok:
                importance, ok = QInputDialog.getInt(
                    self, "Importance", "Importance (1-10):", 5, 1, 10
                )
                if ok:
                    self._memory.add_long_term(text.strip(), category=category, importance=importance)
                    self._load_memories()

    @Slot(int)
    def _delete_memory(self, memory_id: int) -> None:
        """Delete memory."""
        reply = QMessageBox.question(
            self, "Delete Memory",
            "Are you sure you want to delete this memory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes and self._memory.delete_long_term(memory_id):
            self._load_memories()

    @Slot(str)
    def _filter_memories(self, text: str) -> None:
        """Filter memories by search text."""
        if not text:
            self._load_memories()
            return

        self._list.clear()
        memories = self._memory.search_long_term(text, limit=50)

        for memory in memories:
            self._add_memory_item(memory)

        self._stats_label.setText(f"{len(memories)} memories (filtered)")