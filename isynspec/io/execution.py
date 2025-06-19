"""Configuration and management of SYNSPEC execution strategies."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TypeAlias

FileList: TypeAlias = Sequence[Path]


class ExecutionStrategy(Enum):
    """Strategy for executing SYNSPEC calculations.

    Attributes:
        SYNSPEC: Run the default SYNSPEC executable
        CUSTOM: Run a custom specified executable
        RSYNSPEC: Run the RSynspec script
    """

    SYNSPEC = auto()
    CUSTOM = auto()
    RSYNSPEC = auto()


@dataclass
class FileManagementConfig:
    """Configuration for managing input/output files.

    Attributes:
        copy_input_files: Whether to copy input files to working directory
        copy_output_files: Whether to copy output files back
        output_directory: Directory to copy output files to
        input_files: List of input files to copy (if None, copy all required files)
        output_files: List of output files to copy (if None, copy all output files)
    """

    copy_input_files: bool = True
    copy_output_files: bool = False
    output_directory: Path | None = None
    input_files: FileList | None = None
    output_files: FileList | None = None


@dataclass
class ExecutionConfig:
    """Configuration for SYNSPEC execution.

    Attributes:
        strategy: The execution strategy to use
        custom_executable: Path to custom executable (when strategy is CUSTOM)
        rsynspec_script: Path to RSynspec script (when strategy is RSYNSPEC)
        file_management: Configuration for file management
    """

    strategy: ExecutionStrategy = ExecutionStrategy.SYNSPEC
    custom_executable: Path | None = None
    rsynspec_script: Path | None = None
    file_management: FileManagementConfig = field(default_factory=FileManagementConfig)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.strategy == ExecutionStrategy.CUSTOM and not self.custom_executable:
            raise ValueError("must provide custom_executable with CUSTOM strategy")
        if self.strategy == ExecutionStrategy.RSYNSPEC and not self.rsynspec_script:
            raise ValueError("must provide rsynspec_script with RSYNSPEC strategy")

        if (
            self.file_management.copy_output_files
            and not self.file_management.output_directory
        ):
            msg = "must provide output_directory when copy_output_files is True"
            raise ValueError(msg)
