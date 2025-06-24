"""Tests for the configuration module."""

import json
from pathlib import Path

import pytest

from isynspec.core.config import (
    DEFAULT_CONFIG,
    _convert_config_paths_to_strings,
    _convert_paths,
    load_config,
    load_config_str,
)
from isynspec.core.session import ISynspecConfig, ISynspecSession
from isynspec.io.execution import (
    ExecutionConfig,
    ExecutionStrategy,
    FileManagementConfig,
    Shell,
)
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy


@pytest.fixture
def sample_config() -> dict[str, dict]:
    """Create a sample configuration dictionary."""
    return {
        "working_dir": {"strategy": "TEMPORARY", "preserve_temp": True},
        "execution": {
            "strategy": "CUSTOM",
            "custom_executable": "/path/to/synspec",
            "shell": "BASH",
            "file_management": {
                "copy_input_files": True,
                "copy_output_files": True,
                "output_directory": "/path/to/output",
                "input_files": ["input1.dat", "input2.dat"],
                "output_files": ["output1.dat", "output2.dat"],
            },
        },
    }


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
        "model_dir": "/path/to/models",
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
    assert isinstance(converted["model_dir"], Path)
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


def test_working_dir_config_from_dict(sample_config: dict[str, dict]) -> None:
    """Test WorkingDirConfig.from_dict method."""
    config = WorkingDirConfig.from_dict(sample_config["working_dir"])

    assert config.strategy == WorkingDirStrategy.TEMPORARY
    assert config.preserve_temp is True
    assert config.specified_path is None


def test_working_dir_config_from_dict_defaults() -> None:
    """Test WorkingDirConfig.from_dict with empty dict."""
    config = WorkingDirConfig.from_dict({})

    assert config.strategy == WorkingDirStrategy.CURRENT
    assert config.preserve_temp is False
    assert config.specified_path is None


def test_working_dir_config_from_dict_with_specified_path() -> None:
    """Test WorkingDirConfig.from_dict with specified path."""
    config = WorkingDirConfig.from_dict(
        {"strategy": "SPECIFIED", "specified_path": "/path/to/dir"}
    )

    assert config.strategy == WorkingDirStrategy.SPECIFIED
    assert config.specified_path == Path("/path/to/dir")


def test_file_management_config_from_dict(sample_config: dict[str, dict]) -> None:
    """Test FileManagementConfig.from_dict method."""
    # Set up a config with both simple paths and renamed paths
    config_dict = {
        "copy_input_files": True,
        "copy_output_files": True,
        "output_directory": "/path/to/output",
        "input_files": [
            "input1.dat",  # Simple path
            ["input2.dat", "renamed2.dat"],  # Renamed file
            ("input3.dat", None),  # Explicit no rename
        ],
        "output_files": [
            "output1.dat",  # Simple path
            ["output2.dat", "renamed2.dat"],  # Renamed file
            ("output3.dat", None),  # Explicit no rename
        ],
    }

    config = FileManagementConfig.from_dict(config_dict)

    assert config.copy_input_files is True
    assert config.copy_output_files is True
    assert config.output_directory == Path("/path/to/output")

    # Check input files
    assert config.input_files is not None
    assert len(config.input_files) == 3
    assert config.input_files[0] == (Path("input1.dat"), None)
    assert config.input_files[1] == (Path("input2.dat"), Path("renamed2.dat"))
    assert config.input_files[2] == (Path("input3.dat"), None)

    # Check output files
    assert config.output_files is not None
    assert len(config.output_files) == 3
    assert config.output_files[0] == (Path("output1.dat"), None)
    assert config.output_files[1] == (Path("output2.dat"), Path("renamed2.dat"))
    assert config.output_files[2] == (Path("output3.dat"), None)


def test_file_management_config_from_dict_defaults() -> None:
    """Test FileManagementConfig.from_dict with empty dict."""
    config = FileManagementConfig.from_dict({})

    assert config.copy_input_files is True
    assert config.copy_output_files is False
    assert config.output_directory is None
    assert config.input_files is None
    assert config.output_files is None


def test_execution_config_from_dict(sample_config: dict[str, dict]) -> None:
    """Test ExecutionConfig.from_dict method."""
    config = ExecutionConfig.from_dict(sample_config["execution"])

    assert config.strategy == ExecutionStrategy.CUSTOM
    assert config.custom_executable == Path("/path/to/synspec")
    assert config.shell == Shell.BASH
    assert isinstance(config.file_management, FileManagementConfig)


def test_execution_config_from_dict_defaults() -> None:
    """Test ExecutionConfig.from_dict with empty dict."""
    config = ExecutionConfig.from_dict({})

    assert config.strategy == ExecutionStrategy.SYNSPEC
    assert config.custom_executable is None
    assert config.script_path is None
    assert config.shell == Shell.AUTO


def test_isynspec_config_from_dict(sample_config: dict[str, dict]) -> None:
    """Test ISynspecConfig.from_dict method."""
    config = ISynspecConfig.from_dict(sample_config)

    assert isinstance(config.working_dir_config, WorkingDirConfig)
    assert config.working_dir_config.strategy == WorkingDirStrategy.TEMPORARY
    assert isinstance(config.execution_config, ExecutionConfig)
    assert config.execution_config.strategy == ExecutionStrategy.CUSTOM


def test_isynspec_config_from_dict_defaults() -> None:
    """Test ISynspecConfig.from_dict with empty dict."""
    config = ISynspecConfig.from_dict({})

    assert config.working_dir_config.strategy == WorkingDirStrategy.CURRENT
    assert config.execution_config.strategy == ExecutionStrategy.SYNSPEC


def test_session_from_config_file(tmp_path: Path) -> None:
    """Test ISynspecSession.from_config_file method."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "working_dir": {"strategy": "TEMPORARY"},
        "execution": {"strategy": "SYNSPEC", "shell": "AUTO"},
    }
    config_file.write_text(json.dumps(config_data))

    session = ISynspecSession.from_config_file(config_file)
    assert isinstance(session, ISynspecSession)
    assert session.config.working_dir_config.strategy == WorkingDirStrategy.TEMPORARY
    assert session.config.execution_config.strategy == ExecutionStrategy.SYNSPEC
