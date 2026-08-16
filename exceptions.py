"""
Custom exceptions for Martin.
"""


class MartinError(Exception):
    """Base exception for Martin."""


class ConfigurationError(MartinError):
    """Configuration-related errors."""


class AIProviderError(MartinError):
    """AI provider errors."""


class ToolError(MartinError):
    """Tool execution errors."""


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""


class ToolExecutionError(ToolError):
    """Tool execution failed."""


class SafetyError(MartinError):
    """Safety violation errors."""


class MemoryError(MartinError):
    """Memory system errors."""


class VoiceError(MartinError):
    """Voice system errors."""


class ValidationError(MartinError):
    """Input validation errors."""