"""Configuration management for SYNSPEC working directories."""

import tempfile
from enum import Enum, auto
from pathlib import Path
from types import TracebackType
from typing import Self, Type

import platformdirs


class WorkingDirStrategy(Enum):
    """Strategy for determining the SYNSPEC working directory.

    Attributes:
        CURRENT: Use the current working directory
        SPECIFIED: Use a specified directory path
        TEMPORARY: Use a temporary directory
        USER_DATA: Use the user's data directory (platform-specific)
    """

    CURRENT = auto()
    SPECIFIED = auto()
    TEMPORARY = auto()
    USER_DATA = auto()


class WorkingDirectory:
    """Manages the working directory for SYNSPEC operations.

    This class handles the creation, validation, and cleanup of working directories
    based on the configured strategy.
    """

    def __init__(
        self,
        strategy: WorkingDirStrategy = WorkingDirStrategy.CURRENT,
        path: Path | None = None,
        preserve_temp: bool = False,
    ) -> None:
        """Initialize working directory manager.

        Args:
            strategy: Working directory strategy to use.
            path: Path to use when strategy is SPECIFIED.
            preserve_temp: Whether to preserve temporary directories.
        """
        if strategy == WorkingDirStrategy.SPECIFIED and path is None:
            raise ValueError("must provide path when strategy is SPECIFIED")
        self.strategy = strategy
        self.specified_path = path
        self.preserve_temp = preserve_temp
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
        if self.strategy == WorkingDirStrategy.CURRENT:
            self._working_dir = Path.cwd()

        elif self.strategy == WorkingDirStrategy.SPECIFIED:
            assert self.specified_path  # checked in post_init
            path = self.specified_path
            path.mkdir(parents=True, exist_ok=True)
            self._working_dir = path

        elif self.strategy == WorkingDirStrategy.TEMPORARY:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="isynspec_"))
            self._working_dir = self._temp_dir

        elif self.strategy == WorkingDirStrategy.USER_DATA:
            data_dir = Path(platformdirs.user_data_dir("isynspec"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self._working_dir = data_dir

    def cleanup(self) -> None:
        """Clean up temporary resources if necessary."""
        import shutil

        if (
            self._temp_dir is not None
            and self.strategy == WorkingDirStrategy.TEMPORARY
            and not self.preserve_temp
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
