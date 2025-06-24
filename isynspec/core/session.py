"""Main interface for interacting with SYNSPEC."""

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Self, Type

from isynspec.core.config import load_config
from isynspec.io.execution import ExecutionConfig
from isynspec.io.workdir import WorkingDirConfig, WorkingDirectory, WorkingDirStrategy


@dataclass
class ISynspecConfig:
    """Configuration for ISynspec session.

    Attributes:
        working_dir_config: Configuration for working directory management
        execution_config: Configuration for execution strategy and file management
        model_dir: Directory containing model files, if None use current directory
    """

    working_dir_config: WorkingDirConfig = field(
        default_factory=lambda: WorkingDirConfig(strategy=WorkingDirStrategy.CURRENT)
    )
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)
    model_dir: Path | None = None

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> Self:
        """Create an ISynspecConfig instance from a configuration dictionary.

        Args:
            config_dict: Dictionary containing configuration options.

        Returns:
            An instance of ISynspecConfig with the provided settings.
        """
        # In normal usage, these defaults will be overridden by defaults in config.py
        working_dir_config = WorkingDirConfig.from_dict(
            config_dict.get("working_dir", {})
        )
        execution_config = ExecutionConfig.from_dict(config_dict.get("execution", {}))
        model_dir = config_dict.get("model_dir")
        if model_dir is not None:
            model_dir = Path(model_dir)

        return cls(
            working_dir_config=working_dir_config,
            execution_config=execution_config,
            model_dir=model_dir,
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

    def __init__(self, config: ISynspecConfig | None = None) -> None:
        """Initialize a new SYNSPEC session.

        Args:
            config: Configuration options for the session
        """
        self.config = config if config is not None else ISynspecConfig()
        self._working_dir: WorkingDirectory | None = None

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> Self:
        """Create a session from a configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            An instance of ISynspecSession initialized with the provided configuration.
        """
        config = load_config(config_path)
        return cls(config=ISynspecConfig.from_dict(config))

    def _prepare_working_directory(self) -> None:
        """Prepare the working directory with input files if needed."""
        if not self.config.execution_config.file_management.copy_input_files:
            return

        input_files = self.config.execution_config.file_management.input_files
        # TODO: If input_files is None, copy all required files
        # For now, copy specified files
        if input_files:
            for file_path in input_files:
                if file_path.exists():
                    import shutil

                    dst = self.working_dir / file_path.name
                    shutil.copy2(file_path, dst)

    def _collect_output_files(self) -> None:
        """Copy output files to output directory if configured."""
        if not self.config.execution_config.file_management.copy_output_files:
            return

        output_dir = self.config.execution_config.file_management.output_directory
        if not output_dir:
            return

        output_files = self.config.execution_config.file_management.output_files
        # TODO: If output_files is None, copy all output files
        # For now, copy specified files
        if output_files:
            output_dir.mkdir(parents=True, exist_ok=True)
            import shutil

            for file_path in output_files:
                src = self.working_dir / file_path.name
                if src.exists():
                    dst = output_dir / file_path.name
                    shutil.copy2(src, dst)

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
            self._prepare_working_directory()

    def cleanup(self) -> None:
        """Clean up the session resources."""
        if self._working_dir:
            self._collect_output_files()
            self._working_dir.cleanup()
            self._working_dir = None

    def __enter__(self) -> "ISynspecSession":
        """Initialize the session when entering context."""
        self.init()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up when exiting context."""
        self.cleanup()

    def run(self, model: str) -> None:
        """Run SYNSPEC calculation for a given model.

        This method:
        1. Links/copies the model atmosphere file (*.7) as fort.8
        2. Uses the model input file (*.5) as stdin
        3. Redirects stdout to a log file (*.log)

        Args:
            model: Base name of the model files (without extension)

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If required model files are missing
        """
        if not self._working_dir:
            raise RuntimeError(
                "Session not initialized. Use with-statement or call init()"
            )

        if self.config.model_dir:
            model_atm = self.config.model_dir / f"{model}.7"
            model_input = self.config.model_dir / f"{model}.5"
        else:
            model_atm = Path(f"{model}.7")
            model_input = Path(f"{model}.5")

        # Check if model files exist
        if not model_atm.exists():
            raise FileNotFoundError(f"Model atmosphere file not found: {model_atm}")
        if not model_input.exists():
            raise FileNotFoundError(f"Model input file not found: {model_input}")

        # Set up model atmosphere as fort.8
        dst = self.working_dir / "fort.8"
        if dst.exists():
            dst.unlink()

        # Use symlink or copy based on configuration
        if self.config.execution_config.file_management.use_symlinks:
            dst.symlink_to(model_atm)
        else:
            import shutil

            shutil.copy2(model_atm, dst)

        # Run SYNSPEC with stdin from model.5 and stdout to model.log
        from isynspec.io.execution import SynspecExecutor

        executor = SynspecExecutor(
            config=self.config.execution_config,
            working_dir=self.working_dir,
        )

        executor.execute(
            stdin_file=model_input,
            stdout_file=Path(f"{model}.log"),
        )
