"""Configuration management for ISynspec."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Union

from isynspec.utils import convert_dict_value_to_path, deep_update

DEFAULT_CONFIG: dict[str, Any] = {
    "working_dir": {
        "strategy": "CURRENT",
        "specified_path": None,
        "preserve_temp": False,
    },
    "execution": {
        "strategy": "SYNSPEC",
        "custom_executable": None,
        "script_path": None,
        "shell": "AUTO",
        "file_management": {
            "copy_input_files": True,
            "copy_output_files": False,
            "output_directory": None,
            "input_files": None,
            "output_files": None,
        },
    },
}


def load_config(config_path: Union[str, Path]) -> dict[str, Any]:
    """Load configuration from a file.

    Args:
        config_path: Path to configuration file.

    Returns:
        A dictionary with the loaded configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        json.JSONDecodeError: If the config file is not valid JSON.
    """
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        user_config = f.read()

    config_dict = load_config_str(user_config)

    return config_dict


def load_config_str(config_str: str) -> dict[str, Any]:
    """Load configuration from a JSON string.

    Args:
        config_str: JSON string containing the configuration.

    Returns:
        A dictionary with the loaded configuration.

    Raises:
        json.JSONDecodeError: If the config string is not valid JSON.
    """
    config_dict = deepcopy(DEFAULT_CONFIG)

    if config_str:
        deep_update(json.loads(config_str), config_dict)

    config_dict = _convert_paths(config_dict)

    return config_dict


def _convert_paths(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Convert path strings to Path objects in configuration."""
    convert_dict_value_to_path(config_dict, "synspec_path")
    convert_dict_value_to_path(config_dict["working_dir"], "specified_path")
    convert_dict_value_to_path(config_dict["execution"], "custom_executable")
    convert_dict_value_to_path(config_dict["execution"], "script_path")

    file_mgmt = config_dict["execution"]["file_management"]
    convert_dict_value_to_path(file_mgmt, "output_directory")
    convert_dict_value_to_path(file_mgmt, "input_files")
    convert_dict_value_to_path(file_mgmt, "output_files")

    return config_dict


def _convert_config_paths_to_strings(value: Any) -> Union[str, list, dict, Any]:
    """Convert Path objects to strings in configuration value."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_convert_config_paths_to_strings(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _convert_config_paths_to_strings(val) for key, val in value.items()
        }
    return value
