"""
Configuration management for Martin.
Loads and validates configuration from YAML file.
"""
import os
from pathlib import Path
from typing import Any, Self

import yaml


class Config:
    """Singleton configuration manager."""

    _instance: Self | None = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}
            cls._instance._loaded = False
            cls._instance._config_path = None  # type: ignore[assignment]
        return cls._instance

    def __init__(self) -> None:
        pass

    def load(self, config_path: str | None = None) -> None:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = self._find_config_file()

        self._config_path = config_path
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

        self._apply_env_overrides()
        self._loaded = True

    def _find_config_file(self) -> str:
        """Find config.yaml by searching upward from current file."""
        current = Path(__file__).resolve()
        for parent in current.parents:
            config_file = parent / "config" / "config.yaml"
            if config_file.exists():
                return str(config_file)
        # Fallback to default location
        return str(Path.cwd() / "config" / "config.yaml")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            "MARTIN_OLLAMA_URL": ("ai", "ollama_url"),
            "MARTIN_MODEL": ("ai", "model"),
            "MARTIN_LOG_LEVEL": ("logging", "level"),
            "MARTIN_DEBUG": ("app", "debug"),
        }

        for env_var, keys in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested(keys, value)

    def _set_nested(self, keys: tuple[str, ...], value: Any) -> None:
        """Set nested dictionary value."""
        current = self._config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        """Get configuration value by nested keys."""
        if not self._loaded:
            self.load()

        current = self._config
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            if current is None:
                return default
        return current

    def get_section(self, section: str) -> dict[str, Any]:
        """Get entire configuration section."""
        if not self._loaded:
            self.load()
        return self._config.get(section, {})

    def set_config_for_testing(self, config: dict[str, Any]) -> None:
        """Set config directly for testing."""
        self._config = config
        self._loaded = True


def get_config() -> Config:
    """Get global configuration instance."""
    return Config()