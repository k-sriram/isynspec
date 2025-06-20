"""Tests for configuration management."""

import json
import tempfile
from pathlib import Path

import pytest

from isynspec.config import ConfigurationManager
from isynspec.io.execution import ExecutionStrategy, Shell
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy
from isynspec.session import ISynspecConfig


def test_default_config():
    """Test loading default configuration."""
    manager = ConfigurationManager()
    config = manager.load_config()

    assert isinstance(config, ISynspecConfig)
    assert config.synspec_path is None
    assert config.working_dir_config.strategy == WorkingDirStrategy.CURRENT
    assert config.working_dir_config.specified_path is None
    assert config.working_dir_config.preserve_temp is False
    assert config.execution_config.strategy == ExecutionStrategy.SYNSPEC
    assert config.execution_config.shell == Shell.AUTO


def test_load_custom_config():
    """Test loading configuration from file."""
    custom_config = {
        "synspec_path": "/usr/local/bin/synspec",
        "working_dir_config": {
            "strategy": "SPECIFIED",
            "specified_path": "/tmp/synspec",
            "preserve_temp": True,
        },
        "execution": {
            "strategy": "CUSTOM",
            "custom_executable": "/usr/local/bin/custom_synspec",
            "shell": "BASH",
            "file_management": {
                "copy_input_files": False,
                "copy_output_files": True,
                "output_directory": "/tmp/output",
                "input_files": [
                    "/path/to/input1.dat",
                    "/path/to/input2.dat",
                ],
                "output_files": [
                    "/path/to/output1.dat",
                    "/path/to/output2.dat",
                ],
            },
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_config_path = Path(temp_dir) / "config.json"
        with open(temp_config_path, "w") as f:
            f.write(json.dumps(custom_config))

        manager = ConfigurationManager()
        config = manager.load_config(temp_config_path)

        assert config.synspec_path == Path("/usr/local/bin/synspec")
        assert config.working_dir_config.strategy == WorkingDirStrategy.SPECIFIED
        assert config.working_dir_config.specified_path == Path("/tmp/synspec")
        assert config.working_dir_config.preserve_temp is True
        assert config.execution_config.strategy == ExecutionStrategy.CUSTOM
        custom_exec = Path("/usr/local/bin/custom_synspec")
        assert config.execution_config.custom_executable == custom_exec
        assert config.execution_config.shell == Shell.BASH

        file_mgmt = config.execution_config.file_management
        assert file_mgmt.copy_input_files is False
        assert file_mgmt.copy_output_files is True
        assert file_mgmt.output_directory == Path("/tmp/output")
        assert file_mgmt.input_files == [
            Path("/path/to/input1.dat"),
            Path("/path/to/input2.dat"),
        ]
        assert file_mgmt.output_files == [
            Path("/path/to/output1.dat"),
            Path("/path/to/output2.dat"),
        ]


def test_save_config(tmp_path):
    """Test saving configuration to file."""
    config = ISynspecConfig(
        synspec_path=Path("/usr/local/bin/synspec"),
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED,
            specified_path=Path("/tmp/synspec"),
            preserve_temp=True,
        ),
    )

    config_path = tmp_path / "config.json"

    manager = ConfigurationManager()
    manager.save_config(config, config_path)  # Read the saved file and verify contents
    with open(config_path, "r") as f:
        saved_config = json.load(f)

    assert saved_config["synspec_path"] == str(config.synspec_path)

    # Check working directory settings
    working_dir = saved_config["working_dir_config"]
    working_dir_config = config.working_dir_config
    assert working_dir["strategy"] == working_dir_config.strategy.name
    assert working_dir["specified_path"] == str(working_dir_config.specified_path)
    assert working_dir["preserve_temp"] == working_dir_config.preserve_temp


def test_load_nonexistent_file():
    """Test loading from a nonexistent file returns defaults."""
    manager = ConfigurationManager()
    with pytest.raises(FileNotFoundError):
        # Attempt to load a configuration from a file that does not exist
        manager.load_config("nonexistent.json")


def test_save_without_path():
    """Test saving without providing a path."""
    manager = ConfigurationManager()
    config = ISynspecConfig()

    with pytest.raises(ValueError, match="No configuration file path provided"):
        manager.save_config(config)


def test_partial_config_override(tmp_path):
    """Test loading config that only overrides some values."""
    partial_config = {
        "working_dir_config": {
            "strategy": "TEMPORARY",
            "preserve_temp": True,
        }
    }

    config_path = tmp_path / "config.json"
    with config_path.open("w") as f:
        # Write partial config to file
        f.write(json.dumps(partial_config))

    manager = ConfigurationManager()
    config = manager.load_config(config_path)

    # Check overridden values
    assert config.working_dir_config.strategy == WorkingDirStrategy.TEMPORARY
    assert config.working_dir_config.preserve_temp is True

    # Check values that should remain as defaults
    assert config.synspec_path is None
    assert config.execution_config.strategy == ExecutionStrategy.SYNSPEC


def test_invalid_json(tmp_path):
    """Test loading invalid JSON file."""
    config_path = tmp_path / "invalid_config.json"
    with config_path.open("w") as f:
        f.write("invalid json content")

    manager = ConfigurationManager()
    with pytest.raises(json.JSONDecodeError):
        manager.load_config(config_path)


def test_config_path_types(tmp_path):
    """Test different path type inputs."""
    manager = ConfigurationManager()

    config = {
        "synspec_path": "/usr/local/bin/synspec",
        "working_dir_config": {
            "strategy": "CURRENT",
        },
        "execution": {
            "strategy": "SYNSPEC",
            "shell": "AUTO",
        },
    }
    config_path = tmp_path / "config.json"
    with config_path.open("w") as f:
        f.write(json.dumps(config))

    # String path
    config1 = manager.load_config(str(config_path))
    assert isinstance(config1, ISynspecConfig)

    # Path object
    config2 = manager.load_config(Path(config_path))
    assert isinstance(config2, ISynspecConfig)

    # None
    config3 = manager.load_config(None)
    assert isinstance(config3, ISynspecConfig)
