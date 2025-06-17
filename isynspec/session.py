"""Main interface for interacting with SYNSPEC."""

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

from .io.workdir import WorkingDirConfig, WorkingDirectory, WorkingDirStrategy


@dataclass
class ISynspecConfig:
    """Configuration for ISynspec session.

    Attributes:
        synspec_path: Path to the SYNSPEC executable
        working_dir_config: Configuration for working directory management
    """

    synspec_path: Optional[Path] = None
    working_dir_config: WorkingDirConfig = field(
        default_factory=lambda: WorkingDirConfig(strategy=WorkingDirStrategy.CURRENT)
    )


class ISynspecSession:
    """Main interface for running SYNSPEC calculations.

    This class manages the SYNSPEC environment, handles file I/O,
    and provides a high-level API for spectral synthesis.

    Example:
        >>> with ISynspecSession() as synspec:
        ...     synspec.set_model_atmosphere(teff=10000, logg=4.0)
        ...     synspec.set_wavelength_range(start=4000, end=5000)
        ...     spectrum = synspec.calculate_spectrum()
    """

    def __init__(self, config: Optional[ISynspecConfig] = None) -> None:
        """Initialize a new SYNSPEC session.

        Args:
            config: Configuration options for the session
        """
        self.config = config if config is not None else ISynspecConfig()
        self._working_dir: Optional[WorkingDirectory] = None

        # Validate and locate SYNSPEC executable
        self._executable = self._find_synspec_executable()

    def _find_synspec_executable(self) -> Path:
        """Locate the SYNSPEC executable.

        Returns:
            Path to the SYNSPEC executable.

        Raises:
            FileNotFoundError: If SYNSPEC executable cannot be found.
        """
        # First check config
        if self.config.synspec_path:
            if self.config.synspec_path.is_file():
                return self.config.synspec_path
            raise FileNotFoundError(
                f"SYNSPEC executable not found at {self.config.synspec_path}"
            )

        # TODO: Implement search in common locations:
        # 1. Current directory
        # 2. PATH environment
        # 3. Common installation directories
        # 4. Built-in compiled version
        raise NotImplementedError(
            "Automatic SYNSPEC executable discovery not implemented"
        )

    @property
    def working_dir(self) -> Path:
        """Get the current working directory.

        Returns:
            Path to the current working directory.

        Raises:
            RuntimeError: If session is not initialized.
        """
        if not self._working_dir:
            raise RuntimeError(
                "Session not initialized. Use with-statement or call init()"
            )
        return self._working_dir.path

    def init(self) -> None:
        """Initialize the SYNSPEC session.

        This method is called automatically when using the context manager,
        but can be called manually for longer-running sessions.
        """
        if not self._working_dir:
            self._working_dir = WorkingDirectory(self.config.working_dir_config)
            self._working_dir.path  # Initialize the directory

    def cleanup(self) -> None:
        """Clean up the session resources."""
        if self._working_dir:
            self._working_dir.cleanup()
            self._working_dir = None

    def __enter__(self) -> "ISynspecSession":
        """Initialize the session when entering context."""
        self.init()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Clean up when exiting context."""
        self.cleanup()
