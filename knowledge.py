"""
Knowledge page for Martin GUI (placeholder for RAG system).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.gui.theme import DARK_THEME


class KnowledgePage(QWidget):
    """Knowledge page - placeholder for RAG system."""

    def __init__(self) -> None:
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("Knowledge Base")
        title.setStyleSheet(f"font-size: {DARK_THEME.font_size_large + 4}pt; font-weight: bold; color: {DARK_THEME.text_primary};")
        main_layout.addWidget(title)

        # Placeholder content
        placeholder = QFrame()
        placeholder.setObjectName("panel")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(32, 32, 32, 32)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("📚")
        icon.setStyleSheet("font-size: 48pt;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout.addWidget(icon)

        text = QLabel("Knowledge Base (RAG System)\n\nNot yet implemented.\nFuture phase will add document indexing and retrieval.")
        text.setObjectName("secondaryLabel")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)
        placeholder_layout.addWidget(text)

        main_layout.addWidget(placeholder, 1)