"""
Tool registry foundation for Martin.
Defines base tool interface and registry.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar


class SafetyLevel(Enum):
    """Safety level for tools."""
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolResult:
    """Result of tool execution."""
    success: bool
    data: Any = None
    error: str | None = None
    requires_confirmation: bool = False
    confirmation_message: str | None = None


class BaseTool(ABC):
    """Base class for all tools."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    parameters: ClassVar[list[ToolParameter]] = []
    safety_level: ClassVar[SafetyLevel] = SafetyLevel.SAFE
    requires_confirmation: ClassVar[bool] = False

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters."""

    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param.name: {
                        "type": param.type,
                        "description": param.description,
                    }
                    for param in self.parameters
                },
                "required": [
                    param.name for param in self.parameters if param.required
                ],
            },
        }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._enabled_tools: set[str] = set()

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        if not tool.name:
            raise ValueError("Tool must have a name")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)
        self._enabled_tools.discard(name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_enabled(self) -> list[BaseTool]:
        """List enabled tools."""
        return [self._tools[name] for name in self._enabled_tools if name in self._tools]

    def enable(self, name: str) -> bool:
        """Enable a tool."""
        if name in self._tools:
            self._enabled_tools.add(name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a tool."""
        if name in self._enabled_tools:
            self._enabled_tools.remove(name)
            return True
        return False

    def is_enabled(self, name: str) -> bool:
        """Check if tool is enabled."""
        return name in self._enabled_tools

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all enabled tools."""
        return [tool.get_schema() for tool in self.list_enabled()]

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
            )

        if not self.is_enabled(name):
            return ToolResult(
                success=False,
                error=f"Tool '{name}' is not enabled",
            )

        try:
            return tool.execute(**kwargs)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as e:  # noqa: BLE001
            return ToolResult(
                success=False,
                error=str(e),
            )


_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry