"""Configuration management for ISynspec."""

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Union

from isynspec.io.execution import (
    ExecutionConfig,
    ExecutionStrategy,
    FileManagementConfig,
    Shell,
)
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy
from isynspec.session import ISynspecConfig
from isynspec.utils import convert_dict_value_to_path, deep_update

DEFAULT_CONFIG: dict[str, Any] = {
    "synspec_path": None,
    "working_dir_config": {
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


@dataclass
class ConfigurationManager:
    """Manages ISynspec configuration loading and saving.

    This class handles reading configuration from files and provides
    default values when specific parameters are not provided.

    Example:
        >>> config_manager = ConfigurationManager()
        >>> config = config_manager.load_config("config.json")
        >>> session = ISynspecSession(config)
    """

    config_path: Path | None = None

    @staticmethod
    def _convert_paths(config_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert path strings to Path objects in configuration."""
        convert_dict_value_to_path(config_dict, "synspec_path")
        convert_dict_value_to_path(config_dict["working_dir_config"], "specified_path")
        convert_dict_value_to_path(config_dict["execution"], "custom_executable")
        convert_dict_value_to_path(config_dict["execution"], "script_path")

        file_mgmt = config_dict["execution"]["file_management"]
        convert_dict_value_to_path(file_mgmt, "output_directory")
        convert_dict_value_to_path(file_mgmt, "input_files")
        convert_dict_value_to_path(file_mgmt, "output_files")

        return config_dict

    @staticmethod
    def _create_working_dir_config(config_dict: dict[str, Any]) -> WorkingDirConfig:
        """Create WorkingDirConfig from dictionary."""
        working_dir = config_dict["working_dir_config"]
        return WorkingDirConfig(
            strategy=WorkingDirStrategy[working_dir["strategy"]],
            specified_path=working_dir["specified_path"],
            preserve_temp=working_dir["preserve_temp"],
        )

    @staticmethod
    def _create_execution_config(config_dict: dict[str, Any]) -> ExecutionConfig:
        """Create ExecutionConfig from dictionary."""
        execution = config_dict["execution"]
        file_mgmt = execution["file_management"]

        file_management_config = FileManagementConfig(
            copy_input_files=file_mgmt["copy_input_files"],
            copy_output_files=file_mgmt["copy_output_files"],
            output_directory=file_mgmt["output_directory"],
            input_files=file_mgmt["input_files"],
            output_files=file_mgmt["output_files"],
        )

        return ExecutionConfig(
            strategy=ExecutionStrategy[execution["strategy"]],
            custom_executable=execution["custom_executable"],
            script_path=execution["script_path"],
            file_management=file_management_config,
            shell=Shell[execution["shell"]],
        )

    def load_config(self, config_path: Union[str, Path, None] = None) -> ISynspecConfig:
        """Load configuration from a file.

        If no file is provided, uses default configuration.

        Args:
            config_path: Path to configuration file. If None, uses defaults.

        Returns:
            An ISynspecConfig instance with the loaded configuration.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            json.JSONDecodeError: If the config file is not valid JSON.
        """
        self.config_path = Path(config_path) if config_path else None
        config_dict = deepcopy(DEFAULT_CONFIG)

        if self.config_path:
            with open(self.config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                deep_update(user_config, config_dict)

        config_dict = self._convert_paths(config_dict)

        return ISynspecConfig(
            synspec_path=config_dict.get("synspec_path"),
            working_dir_config=self._create_working_dir_config(config_dict),
            execution_config=self._create_execution_config(config_dict),
        )

    def save_config(
        self, config: ISynspecConfig, config_path: Union[str, Path, None] = None
    ) -> None:
        """Save configuration to a file.

        Args:
            config: The configuration to save.
            config_path: Path to save the configuration to. If None, uses the path
                from which the configuration was loaded.

        Raises:
            ValueError: If no config_path is provided and none was used to load.
        """
        save_path = Path(config_path) if config_path else self.config_path
        if not save_path:
            raise ValueError("No configuration file path provided")

        # Convert dataclass to dict
        config_dict = asdict(config)
        assert isinstance(config_dict["working_dir_config"], dict)

        # Convert Path objects to strings
        config_dict = self._convert_config_paths_to_strings(config_dict)  # type: ignore

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4)

    def _convert_config_paths_to_strings(
        self, value: Any
    ) -> Union[str, list, dict, Any]:
        """Convert Path objects to strings in configuration value."""
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, list):
            return [self._convert_config_paths_to_strings(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self._convert_config_paths_to_strings(val)
                for key, val in value.items()
            }
        return value
