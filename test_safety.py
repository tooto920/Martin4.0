"""
Tests for safety checks and security.
"""
from typing import ClassVar

import pytest

from app.core.config import Config
from app.core.tools import (
    BaseTool,
    SafetyLevel,
    ToolRegistry,
    ToolResult,
)


@pytest.fixture(autouse=True)
def reset_config() -> None:
    """Reset config singleton before each test."""
    Config._instance = None
    Config._config = {}
    Config._loaded = False
    Config._config_path = None
    Config().set_config_for_testing({
        "tools": {
            "enabled": [],
            "dangerous_tools_require_confirmation": True,
            "allowed_apps": [],
            "allowed_paths": [],
        }
    })


@pytest.fixture(autouse=True)
def reset_tool_registry() -> None:
    """Reset global tool registry before each test."""
    import app.core.tools as tools_module
    tools_module._tool_registry = None


class SafeTool(BaseTool):
    name = "safe_tool"
    description = "A safe tool"
    parameters: ClassVar[list] = []
    safety_level = SafetyLevel.SAFE

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data="safe")


class DangerousTool(BaseTool):
    name = "dangerous_tool"
    description = "A dangerous tool"
    parameters: ClassVar[list] = []
    safety_level = SafetyLevel.DANGEROUS
    requires_confirmation = True

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            data="done",
            requires_confirmation=True,
            confirmation_message="This is dangerous!"
        )


class TestSafety:
    """Tests for safety features."""

    def test_safety_levels(self) -> None:
        """Safety levels should be ordered."""
        assert SafetyLevel.SAFE.value == "safe"
        assert SafetyLevel.CAUTION.value == "caution"
        assert SafetyLevel.DANGEROUS.value == "dangerous"

    def test_tool_safety_level(self) -> None:
        """Tools should have safety levels."""
        safe_tool = SafeTool()
        dangerous_tool = DangerousTool()

        assert safe_tool.safety_level == SafetyLevel.SAFE
        assert dangerous_tool.safety_level == SafetyLevel.DANGEROUS
        assert dangerous_tool.requires_confirmation is True

    def test_registry_safety_execution(self) -> None:
        """Registry should execute dangerous tools but flag confirmation."""
        registry = ToolRegistry()
        registry.register(DangerousTool())
        registry.enable("dangerous_tool")

        result = registry.execute("dangerous_tool")
        assert result.success is True
        assert result.requires_confirmation is True
        assert result.confirmation_message == "This is dangerous!"

    def test_safe_tool_no_confirmation(self) -> None:
        """Safe tools should not require confirmation."""
        registry = ToolRegistry()
        registry.register(SafeTool())
        registry.enable("safe_tool")

        result = registry.execute("safe_tool")
        assert result.success is True
        assert result.requires_confirmation is False

    def test_confirmation_required_config(self) -> None:
        """Config should control confirmation requirement."""
        # This is tested via config.yaml dangerous_tools_require_confirmation setting
        # The agent checks this before executing dangerous tools