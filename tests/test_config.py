"""Tests for the configuration module."""

import json
from pathlib import Path

import pytest

from isynspec.config import (
    DEFAULT_CONFIG,
    _convert_config_paths_to_strings,
    _convert_paths,
    load_config,
    load_config_str,
)


def test_load_config_str_empty():
    """Test loading empty configuration string."""
    config = load_config_str("")
    assert config == _convert_paths(DEFAULT_CONFIG.copy())


def test_load_config_str_with_data():
    """Test loading configuration from a JSON string."""
    custom_config = {
        "working_dir": {
            "strategy": "SPECIFIED",
            "specified_path": "/path/to/dir",
        }
    }
    config = load_config_str(json.dumps(custom_config))

    # Check that default values are preserved
    assert config["working_dir"]["preserve_temp"] is False
    # Check that our custom values are set
    assert config["working_dir"]["strategy"] == "SPECIFIED"
    assert isinstance(config["working_dir"]["specified_path"], Path)
    assert config["working_dir"]["specified_path"] == Path("/path/to/dir")


def test_load_config_str_invalid_json():
    """Test loading invalid JSON string."""
    with pytest.raises(json.JSONDecodeError):
        load_config_str("{invalid json")


def test_load_config_file(tmp_path):
    """Test loading configuration from a file."""
    config_file = tmp_path / "config.json"
    custom_config = {
        "execution": {
            "custom_executable": "/path/to/exe",
            "file_management": {
                "output_directory": "/path/to/output",
                "input_files": ["/path/to/input1", "/path/to/input2"],
            },
        }
    }

    config_file.write_text(json.dumps(custom_config))

    config = load_config(config_file)

    # Check path conversions
    assert isinstance(config["execution"]["custom_executable"], Path)
    assert config["execution"]["custom_executable"] == Path("/path/to/exe")

    # Check file management paths
    file_mgmt = config["execution"]["file_management"]
    assert isinstance(file_mgmt["output_directory"], Path)
    assert file_mgmt["output_directory"] == Path("/path/to/output")
    assert all(isinstance(p, Path) for p in file_mgmt["input_files"])
    input_paths = ["/path/to/input1", "/path/to/input2"]
    assert file_mgmt["input_files"] == [Path(p) for p in input_paths]


def test_load_config_file_not_found():
    """Test loading configuration from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.json")


def test_convert_paths():
    """Test path conversion in configuration."""
    config = {
        "synspec_path": "/path/to/synspec",
        "working_dir": {"specified_path": "/path/to/workdir"},
        "execution": {
            "custom_executable": "/path/to/exe",
            "script_path": "/path/to/script",
            "file_management": {
                "output_directory": "/path/to/output",
                "input_files": ["/path/to/input1", "/path/to/input2"],
                "output_files": ["/path/to/output1"],
            },
        },
    }

    converted = _convert_paths(config)
    file_mgmt = converted["execution"]["file_management"]

    # Check all paths are converted
    assert isinstance(converted["synspec_path"], Path)
    assert isinstance(converted["working_dir"]["specified_path"], Path)
    assert isinstance(converted["execution"]["custom_executable"], Path)
    assert isinstance(converted["execution"]["script_path"], Path)
    assert isinstance(file_mgmt["output_directory"], Path)
    assert all(isinstance(p, Path) for p in file_mgmt["input_files"])
    assert all(isinstance(p, Path) for p in file_mgmt["output_files"])


def test_convert_config_paths_to_strings():
    """Test converting Path objects back to strings."""
    config = {
        "path": Path("/some/path"),
        "paths": [Path("/path1"), Path("/path2")],
        "nested": {"path": Path("/nested/path"), "other": "value"},
    }

    result = _convert_config_paths_to_strings(config)

    assert isinstance(result, dict)
    assert isinstance(result["path"], str)
    assert isinstance(result["paths"], list)
    assert all(isinstance(p, str) for p in result["paths"])
    assert isinstance(result["nested"]["path"], str)
    assert isinstance(result["nested"]["other"], str)
    assert result["path"] == str(Path("/some/path"))
    assert result["paths"] == [str(Path("/path1")), str(Path("/path2"))]
    assert result["nested"]["path"] == str(Path("/nested/path"))
    assert result["nested"]["other"] == "value"
