"""
Tests for memory system.
"""
import os
import tempfile

import pytest

from app.core.config import Config
from app.memory.database import MemoryDatabase
from app.memory.memory import MemoryManager


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset config singleton before each test."""
    Config._instance = None
    Config._config = {}
    Config._loaded = False
    Config._config_path = None
    Config().set_config_for_testing({
        "memory": {
            "database_path": "test.db",
            "short_term_max_messages": 20,
            "long_term_enabled": True,
        }
    })


class TestMemoryDatabase:
    """Tests for MemoryDatabase."""

    @pytest.fixture
    def db(self) -> MemoryDatabase:
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        db = MemoryDatabase(temp_path)
        yield db
        os.unlink(temp_path)

    def test_add_memory(self, db: MemoryDatabase) -> None:
        """Should add memory and return ID."""
        memory_id = db.add_memory("Test memory", "test", 5)
        assert memory_id > 0

    def test_get_memories(self, db: MemoryDatabase) -> None:
        """Should retrieve memories."""
        db.add_memory("Memory 1", "cat1", 1)
        db.add_memory("Memory 2", "cat1", 2)
        db.add_memory("Memory 3", "cat2", 3)

        memories = db.get_memories(category="cat1")
        assert len(memories) == 2
        assert memories[0]["importance"] == 2
        assert memories[1]["importance"] == 1

    def test_search_memories(self, db: MemoryDatabase) -> None:
        """Should search memories by content."""
        db.add_memory("Important information about Python", "tech", 5)
        db.add_memory("Random text", "general", 1)

        results = db.search_memories("Python")
        assert len(results) == 1
        assert "Python" in results[0]["content"]

    def test_delete_memory(self, db: MemoryDatabase) -> None:
        """Should delete memory by ID."""
        memory_id = db.add_memory("To delete", "test", 1)
        assert db.delete_memory(memory_id) is True
        assert db.delete_memory(9999) is False

    def test_update_memory(self, db: MemoryDatabase) -> None:
        """Should update memory fields."""
        memory_id = db.add_memory("Original", "cat1", 1)
        assert db.update_memory(memory_id, content="Updated", importance=5) is True

        memories = db.get_memories()
        updated = next(m for m in memories if m["id"] == memory_id)
        assert updated["content"] == "Updated"
        assert updated["importance"] == 5

    def test_conversations(self, db: MemoryDatabase) -> None:
        """Should store and retrieve conversations."""
        db.add_conversation("session1", "user", "Hello")
        db.add_conversation("session1", "assistant", "Hi there")

        conv = db.get_conversation("session1")
        assert len(conv) == 2
        # Check both messages are present (order may vary with same timestamp)
        roles = [msg["role"] for msg in conv]
        assert "user" in roles
        assert "assistant" in roles
        contents = [msg["content"] for msg in conv]
        assert "Hello" in contents
        assert "Hi there" in contents

        db.clear_conversation("session1")
        conv = db.get_conversation("session1")
        assert len(conv) == 0


class TestMemoryManager:
    """Tests for MemoryManager."""

    @pytest.fixture
    def manager(self) -> MemoryManager:
        """Create memory manager with temp database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = f.name
        manager = MemoryManager("test_session")
        manager._db = MemoryDatabase(temp_path)
        yield manager
        os.unlink(temp_path)

    def test_short_term(self, manager: MemoryManager) -> None:
        """Should manage short-term memory."""
        manager.add_short_term("user", "Hello")
        manager.add_short_term("assistant", "Hi")

        history = manager.get_short_term()
        assert len(history) == 2
        assert history[0]["role"] == "user"

    def test_short_term_limit(self, manager: MemoryManager) -> None:
        """Should limit short-term memory size."""
        manager._max_short_term = 3
        for i in range(5):
            manager.add_short_term("user", f"Message {i}")

        history = manager.get_short_term()
        assert len(history) == 3
        assert history[0]["content"] == "Message 2"

    def test_long_term(self, manager: MemoryManager) -> None:
        """Should manage long-term memory."""
        memory_id = manager.add_long_term("Important fact", "facts", 5)
        assert memory_id > 0

        memories = manager.get_long_term(category="facts")
        assert len(memories) == 1
        assert memories[0]["content"] == "Important fact"

    def test_search_long_term(self, manager: MemoryManager) -> None:
        """Should search long-term memories."""
        manager.add_long_term("Python is a programming language", "tech", 3)
        manager.add_long_term("Java is also a language", "tech", 2)

        results = manager.search_long_term("Python")
        assert len(results) == 1
        assert "Python" in results[0]["content"]

    def test_delete_long_term(self, manager: MemoryManager) -> None:
        """Should delete long-term memory."""
        memory_id = manager.add_long_term("To delete", "test", 1)
        assert manager.delete_long_term(memory_id) is True
        assert manager.delete_long_term(9999) is False

    def test_context_for_ai(self, manager: MemoryManager) -> None:
        """Should format context for AI."""
        manager.add_short_term("user", "Hello")
        manager.add_short_term("assistant", "Hi")

        context = manager.get_context_for_ai(5)
        assert len(context) == 2
        assert all("role" in msg and "content" in msg for msg in context)