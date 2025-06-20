"""Configuration management for SYNSPEC working directories."""

import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import TracebackType
from typing import Self, Type

import platformdirs


class WorkingDirStrategy(StrEnum):
    """Strategy for determining the SYNSPEC working directory.

    Attributes:
        CURRENT: Use the current working directory
        SPECIFIED: Use a specified directory path
        TEMPORARY: Use a temporary directory
        USER_DATA: Use the user's data directory (platform-specific)
    """

    CURRENT = "CURRENT"
    SPECIFIED = "SPECIFIED"
    TEMPORARY = "TEMPORARY"
    USER_DATA = "USER_DATA"


@dataclass
class WorkingDirConfig:
    """Configuration for SYNSPEC working directory.

    Attributes:
        strategy: The strategy to use for determining the working directory
        specified_path: Path to use when strategy is SPECIFIED
        preserve_temp: Whether to preserve temporary directories
    """

    strategy: WorkingDirStrategy
    specified_path: str | Path | None = None
    preserve_temp: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.strategy == WorkingDirStrategy.SPECIFIED and not self.specified_path:
            raise ValueError("must provide specified_path with SPECIFIED strategy")

        if self.specified_path and isinstance(self.specified_path, str):
            self.specified_path = Path(self.specified_path)


class WorkingDirectory:
    """Manages the working directory for SYNSPEC operations.

    This class handles the creation, validation, and cleanup of working directories
    based on the configured strategy.
    """

    def __init__(self, config: WorkingDirConfig | None = None) -> None:
        """Initialize working directory manager.

        Args:
            config: Working directory configuration. If None, uses CURRENT strategy.
        """
        self.config = config or WorkingDirConfig(strategy=WorkingDirStrategy.CURRENT)
        self._temp_dir: Path | None = None
        self._working_dir: Path | None = None

    @property
    def path(self) -> Path:
        """Get the current working directory path.

        Returns:
            Path to the working directory.

        Raises:
            RuntimeError: If working directory hasn't been initialized.
        """
        if not self._working_dir:
            self._initialize_working_dir()
        assert self._working_dir is not None  # for type checker
        return self._working_dir

    def _initialize_working_dir(self) -> None:
        """Initialize the working directory based on the configured strategy."""
        if self.config.strategy == WorkingDirStrategy.CURRENT:
            self._working_dir = Path.cwd()

        elif self.config.strategy == WorkingDirStrategy.SPECIFIED:
            assert self.config.specified_path  # checked in post_init
            path = Path(self.config.specified_path)
            path.mkdir(parents=True, exist_ok=True)
            self._working_dir = path

        elif self.config.strategy == WorkingDirStrategy.TEMPORARY:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="isynspec_"))
            self._working_dir = self._temp_dir

        elif self.config.strategy == WorkingDirStrategy.USER_DATA:
            data_dir = Path(platformdirs.user_data_dir("isynspec"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self._working_dir = data_dir

    def cleanup(self) -> None:
        """Clean up temporary resources if necessary."""
        import shutil

        if (
            self._temp_dir is not None
            and self.config.strategy == WorkingDirStrategy.TEMPORARY
            and not self.config.preserve_temp
        ):
            shutil.rmtree(self._temp_dir)
            self._temp_dir = None
            self._working_dir = None

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()
