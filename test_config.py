"""
Tests for configuration management.
"""
import os
import tempfile

from app.core.config import Config, get_config


class TestConfig:
    """Tests for Config class."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        Config._instance = None
        Config._config = {}
        Config._loaded = False
        Config._config_path = None

    def test_singleton(self) -> None:
        """Config should be a singleton."""
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    def test_load_yaml(self) -> None:
        """Config should load from YAML file."""
        yaml_content = """
ai:
  model: "test-model"
  ollama_url: "http://test:11434"
logging:
  level: "DEBUG"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = Config()
            config.load(temp_path)
            assert config.get("ai", "model") == "test-model"
            assert config.get("ai", "ollama_url") == "http://test:11434"
            assert config.get("logging", "level") == "DEBUG"
        finally:
            os.unlink(temp_path)

    def test_get_with_default(self) -> None:
        """Config.get should return default for missing keys."""
        config = Config()
        config.set_config_for_testing({"existing": {"key": "value"}})
        assert config.get("missing", "key", default="default") == "default"
        assert config.get("existing", "key") == "value"

    def test_get_section(self) -> None:
        """Config.get_section should return entire section."""
        config = Config()
        config.set_config_for_testing({"section": {"a": 1, "b": 2}})
        section = config.get_section("section")
        assert section == {"a": 1, "b": 2}
        assert config.get_section("missing") == {}

    def test_env_override(self) -> None:
        """Environment variables should override config."""
        os.environ["MARTIN_MODEL"] = "env-model"
        os.environ["MARTIN_OLLAMA_URL"] = "http://env:11434"

        try:
            yaml_content = "ai:\n  model: \"file-model\"\n  ollama_url: \"http://file:11434\"\n"
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                f.write(yaml_content)
                temp_path = f.name

            config = Config()
            config.load(temp_path)
            assert config.get("ai", "model") == "env-model"
            assert config.get("ai", "ollama_url") == "http://env:11434"
        finally:
            os.unlink(temp_path)
            del os.environ["MARTIN_MODEL"]
            del os.environ["MARTIN_OLLAMA_URL"]

    def test_get_config_function(self) -> None:
        """get_config should return Config instance."""
        config = get_config()
        assert isinstance(config, Config)