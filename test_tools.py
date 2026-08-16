"""
Tests for tool registry.
"""
from typing import ClassVar

import pytest

from app.core.config import Config
from app.core.tools import (
    BaseTool,
    SafetyLevel,
    ToolParameter,
    ToolRegistry,
    ToolResult,
    get_tool_registry,
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


class DummyTool(BaseTool):
    """Dummy tool for testing."""

    name = "dummy"
    description = "A dummy tool"
    parameters: ClassVar[list[ToolParameter]] = [
        ToolParameter(name="param1", type="string", description="First param"),
        ToolParameter(name="param2", type="integer", description="Second param", required=False, default=42),
    ]
    safety_level = SafetyLevel.SAFE

    def execute(self, **kwargs: str) -> ToolResult:
        return ToolResult(success=True, data={"received": kwargs})


class DangerousTool(BaseTool):
    """Dangerous tool for testing."""

    name = "dangerous"
    description = "A dangerous tool"
    parameters: ClassVar[list] = []
    safety_level = SafetyLevel.DANGEROUS
    requires_confirmation = True

    def execute(self, **kwargs: str) -> ToolResult:
        return ToolResult(success=True, data="done", requires_confirmation=True, confirmation_message="Are you sure?")


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_get(self) -> None:
        """Should register and retrieve tools."""
        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)

        retrieved = registry.get("dummy")
        assert retrieved is tool

    def test_unregister(self) -> None:
        """Should unregister tools."""
        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)
        registry.unregister("dummy")

        assert registry.get("dummy") is None

    def test_enable_disable(self) -> None:
        """Should enable and disable tools."""
        registry = ToolRegistry()
        tool = DummyTool()
        registry.register(tool)

        assert registry.enable("dummy") is True
        assert registry.is_enabled("dummy") is True
        assert registry.disable("dummy") is True
        assert registry.is_enabled("dummy") is False

    def test_list_tools(self) -> None:
        """Should list all registered tools."""
        registry = ToolRegistry()
        registry.register(DummyTool())
        registry.register(DangerousTool())

        tools = registry.list_tools()
        assert len(tools) == 2

    def test_list_enabled(self) -> None:
        """Should list only enabled tools."""
        registry = ToolRegistry()
        registry.register(DummyTool())
        registry.register(DangerousTool())
        registry.enable("dummy")

        enabled = registry.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "dummy"

    def test_get_schemas(self) -> None:
        """Should get schemas for enabled tools."""
        registry = ToolRegistry()
        registry.register(DummyTool())
        registry.enable("dummy")

        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "dummy"
        assert "parameters" in schemas[0]

    def test_execute_success(self) -> None:
        """Should execute tool successfully."""
        registry = ToolRegistry()
        registry.register(DummyTool())
        registry.enable("dummy")

        result = registry.execute("dummy", param1="test")
        assert result.success is True
        assert result.data == {"received": {"param1": "test"}}

    def test_execute_not_found(self) -> None:
        """Should return error for unknown tool."""
        registry = ToolRegistry()

        result = registry.execute("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    def test_execute_disabled(self) -> None:
        """Should return error for disabled tool."""
        registry = ToolRegistry()
        registry.register(DummyTool())
        # Not enabled

        result = registry.execute("dummy")
        assert result.success is False
        assert "not enabled" in result.error

    def test_global_registry(self) -> None:
        """Global registry should be singleton."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2