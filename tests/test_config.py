"""Tests for the config module."""

import yaml

from pipeline.config import get_required_columns, load_config, validate_config


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self):
        config = load_config()
        assert "input_path" in config
        assert "output_path" in config
        assert "columns" in config

    def test_loads_yaml_config(self, tmp_path):
        config_data = {"input_path": "custom/input.csv", "batch_size": 500}
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_config(str(config_file))
        assert config["input_path"] == "custom/input.csv"
        assert config["batch_size"] == 500

    def test_default_config_has_required_keys(self):
        config = load_config()
        assert validate_config(config) is True


class TestValidateConfig:
    def test_valid_config(self):
        config = {
            "input_path": "a.csv",
            "output_path": "b.csv",
            "columns": {"required": ["id"]},
        }
        assert validate_config(config) is True

    def test_missing_key(self):
        config = {"input_path": "a.csv"}
        assert validate_config(config) is False


class TestGetRequiredColumns:
    def test_returns_required_columns(self):
        config = {"columns": {"required": ["id", "date", "amount"]}}
        assert get_required_columns(config) == ["id", "date", "amount"]
