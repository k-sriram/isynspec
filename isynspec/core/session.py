"""Main interface for interacting with SYNSPEC."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Self, Type

from isynspec.core.config import load_config
from isynspec.io.execution import ExecutionConfig, SynspecExecutor
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

    def _prepare_working_directory(self, model: str) -> None:
        """Prepare the working directory with input files if needed.

        Args:
            model: Base name of the model files (without extension)
        """
        if not self.config.execution_config.file_management.copy_input_files:
            return

        input_files = self.config.execution_config.file_management.input_files
        # TODO: If input_files is None, copy all required files
        # For now, copy specified files
        if input_files:
            for source_path, rename_path in input_files:
                # Format any path strings that contain {model}
                source = Path(str(source_path).format(model=model))
                if rename_path:
                    rename = Path(str(rename_path).format(model=model))
                else:
                    rename = None

                if source.exists():
                    # Use the renamed path if provided, otherwise use original filename
                    dst_name = rename.name if rename else source.name
                    dst = self.working_dir / dst_name
                    shutil.copy2(source, dst)

    def _collect_output_files(self, model: str) -> None:
        """Copy output files to output directory if configured.

        If output_files is not specified in the configuration, the following default
        mappings will be used:
            - fort.7 -> {model}.spec (main spectrum output)
            - fort.17 -> {model}.cont (continuum data)
            - fort.12 -> {model}.iden (line identifications)
            - fort.16 -> {model}.eqws (equivalent widths)

        Args:
            model: Base name of the model files (without extension)
        """
        if not self.config.execution_config.file_management.copy_output_files:
            return

        output_dir = self.config.execution_config.file_management.output_directory
        if not output_dir:
            return

        output_files = self.config.execution_config.file_management.output_files
        # If output_files is None, use default mapping
        if output_files is None:
            output_files = [
                (Path("fort.7"), Path(f"{model}.spec")),  # Main spectrum output
                (Path("fort.17"), Path(f"{model}.cont")),  # Continuum data
                (Path("fort.12"), Path(f"{model}.iden")),  # Line identifications
                (Path("fort.16"), Path(f"{model}.eqws")),  # Equivalent widths
            ]

        output_dir.mkdir(parents=True, exist_ok=True)

        for source_path, rename_path in output_files:
            # Format any path strings that contain {model}
            source = Path(str(source_path).format(model=model))
            if rename_path:
                rename = Path(str(rename_path).format(model=model))
            else:
                rename = None

            # For output collection, source_path is the name in the working dir
            src = self.working_dir / source.name
            if src.exists():
                # Use the renamed path if provided, otherwise use original filename
                dst_name = rename.name if rename else source.name
                dst = output_dir / dst_name
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

    def init(self, model: str | None = None) -> None:
        """Initialize the SYNSPEC session.

        This method is called automatically when using the context manager,
        but can be called manually for longer-running sessions.

        Args:
            model: Base name of the model files (without extension). Required if using
                  file management with paths containing {model} placeholders.
        """
        if not self._working_dir:
            self._working_dir = WorkingDirectory(self.config.working_dir_config)
            self._working_dir.path  # Initialize the directory
            if model is not None:
                self._prepare_working_directory(model)

    def cleanup(self, model: str | None = None) -> None:
        """Clean up the session resources.

        Args:
            model: Base name of the model files (without extension). Required if using
                  file management with paths containing {model} placeholders.
        """
        if self._working_dir:
            if model is not None:
                self._collect_output_files(model)
            self._working_dir.cleanup()
            self._working_dir = None

    def __enter__(self) -> "ISynspecSession":
        """Initialize the session when entering context."""
        self.init()  # Model will be provided in run()
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up when exiting context."""
        self.cleanup()  # No model needed if we're exiting context

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
            shutil.copy2(model_atm, dst)

        # Run SYNSPEC with stdin from model.5 and stdout to model.log
        executor = SynspecExecutor(
            config=self.config.execution_config,
            working_dir=self.working_dir,
        )

        executor.execute(
            stdin_file=model_input,
            stdout_file=Path(f"{model}.log"),
        )
