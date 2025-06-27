"""Main interface for interacting with SYNSPEC."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Self, Type

import numpy as np

from isynspec.core.config import load_config
from isynspec.io.execution import ExecutionConfig, SynspecExecutor
from isynspec.io.fort7 import Fort7
from isynspec.io.fort16 import Fort16
from isynspec.io.fort17 import Fort17
from isynspec.io.fort19 import Fort19
from isynspec.io.fort55 import Fort55
from isynspec.io.fort56 import Fort56
from isynspec.io.input import InputData
from isynspec.io.workdir import WorkingDirConfig, WorkingDirectory, WorkingDirStrategy


@dataclass
class ISynspecConfig:
    """Configuration for ISynspec session.

    Attributes:
        working_dir_config: Configuration for working directory management
        execution_config: Configuration for execution strategy and file management
        model_dir: Directory containing model files, if None use current directory
        data_dir: Directory containing SYNSPEC data files
    """

    working_dir_config: WorkingDirConfig = field(
        default_factory=lambda: WorkingDirConfig(strategy=WorkingDirStrategy.CURRENT)
    )
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)
    model_dir: Path | None = None
    data_dir: Path | None = None

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

        data_dir = config_dict.get("data_dir")
        if data_dir is not None:
            data_dir = Path(data_dir)

        return cls(
            working_dir_config=working_dir_config,
            execution_config=execution_config,
            model_dir=model_dir,
            data_dir=data_dir,
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

    def _prepare_working_directory(self, model: str, model_atm: Path | None) -> None:
        """Prepare the working directory with input files if needed.

        Args:
            model: Base name of the model files (without extension)
            model_atm: Path to the model atmosphere file
        """
        # Copy or link the model atmosphere file
        if model_atm is not None:
            dst_atm = self.working_dir / "fort.8"
            if dst_atm.exists():
                dst_atm.unlink()
            if self.config.execution_config.file_management.use_symlinks:
                dst_atm.symlink_to(model_atm)
            else:
                shutil.copy2(model_atm, dst_atm)

        if not self.config.execution_config.file_management.copy_input_files:
            return

        # Create data directory link if configured
        if self.config.data_dir is not None:
            data_dir = self.working_dir / "data"
            if not data_dir.exists():
                data_dir.symlink_to(self.config.data_dir, target_is_directory=True)

        input_files = self.config.execution_config.file_management.input_files
        if input_files is None:
            input_files = []
        # TODO: If input_files is None, copy all required files
        # For now, copy specified files

        link = self.config.execution_config.file_management.use_symlinks
        self._copy_files(
            input_files,
            None,
            self.working_dir,
            link=link,
            substitutions={"model": model},
        )

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
            output_dir = Path.cwd()

        output_files: list[tuple[Path, Path | None]] | None = (
            self.config.execution_config.file_management.output_files
        )
        # If output_files is None, use default mapping
        if output_files is None:
            output_files = [
                (Path("fort.7"), Path(f"{model}.spec")),  # Main spectrum output
                (Path("fort.17"), Path(f"{model}.cont")),  # Continuum data
                (Path("fort.12"), Path(f"{model}.iden")),  # Line identifications
                (Path("fort.16"), Path(f"{model}.eqws")),  # Equivalent widths
            ]

        output_dir.mkdir(parents=True, exist_ok=True)

        self._copy_files(
            output_files,
            self.working_dir,
            output_dir,
            link=False,
            substitutions={"model": model},
        )

    def _copy_files(
        self,
        files: list[tuple[Path, Path | None]],
        src_dir: Path | None,
        dst_dir: Path | None,
        link: bool = False,
        substitutions: dict[str, str] = {},
    ) -> None:
        """Copy files from source to destination with optional renaming.

        Args:
            files: List of tuples (source_path, rename_path)
            src_dir: Source directory where files are located
            dst_dir: Destination directory where files should be copied
            link: If True, create symlinks instead of copying files
            substitutions: Dictionary for string substitutions in file paths
        """
        if src_dir is None:
            src_dir = Path.cwd()
        if dst_dir is None:
            dst_dir = Path.cwd()

        for source_file, rename_file in files:
            # Apply substitutions to source path
            source_file = Path(str(source_file).format(**substitutions))
            if rename_file is None:
                rename_file = Path(source_file.name)
            rename_file = Path(str(rename_file).format(**substitutions))
            if not Path(source_file).is_absolute():
                source_file = src_dir / source_file
            else:
                source_file = Path(source_file)
            dest_file = dst_dir / rename_file

            if dest_file == source_file:
                # If source and destination are the same, skip copying
                continue
            if dest_file.exists():
                # If destination file exists, remove it first
                dest_file.unlink()
            # Copy the file or create a symlink
            if link:
                dest_file.symlink_to(source_file)
            else:
                shutil.copy2(source_file, dest_file)

    def _validate_working_dir(self, model: str) -> None:
        """Validate that the working directory contains required files.

        Args:
            model: Base name of the model files (without extension)

        Raises:
            RuntimeError: If working directory is not initialized
            FileNotFoundError: If required model files are missing
        """
        # Check for fort.8 (model atmosphere)
        if not (self.working_dir / "fort.8").exists():
            raise FileNotFoundError("Required file fort.8 not found")

        # Check for fort.55
        fort55_path = self.working_dir / "fort.55"
        if not fort55_path.exists():
            raise FileNotFoundError("Required file fort.55 not found")

        # Check for fort.19 (line list)
        if not (self.working_dir / "fort.19").exists():
            raise FileNotFoundError("Required file fort.19 not found")

        # Check fort.56 only if needed (when ichemc = 1 in fort.55)
        fort55 = Fort55.read(self.working_dir)
        if fort55.ichemc == 1 and not (self.working_dir / "fort.56").exists():
            raise FileNotFoundError("Required file fort.56 not found")

        # Check for data directory
        data_dir = self.working_dir / "data"
        if not data_dir.exists():
            raise FileNotFoundError(f"Required data directory {data_dir} not found")

        # Check for nst file if in model_input
        if self.config.model_dir:
            model_input = self.config.model_dir / f"{model}.5"
        else:
            model_input = Path(f"{model}.5")

        input_data = InputData.from_file(model_input)
        if input_data.nst_filename:
            nst_file = self.working_dir / input_data.nst_filename
            if not nst_file.exists():
                raise FileNotFoundError(f"Required NST file {nst_file} not found")

    @property
    def working_dir(self) -> Path:
        """Get the current working directory.

        Returns:
            Path to the current working directory

        Raises:
            RuntimeError: If session is not initialized
        """
        if not self._working_dir:
            raise RuntimeError("Session not initialized")
        return self._working_dir.path

    def read_fort7(self) -> Fort7:
        """Read and parse the fort.7 file from the working directory.

        This is an output file written by SYNSPEC containing the computed spectrum.

        Returns:
            Fort7: Contents of the fort.7 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.7 does not exist
        """
        return Fort7.read(directory=self.working_dir)

    def read_fort16(self) -> Fort16:
        """Read and parse the fort.16 file from the working directory.

        This is an output file written by SYNSPEC containing equivalent widths.

        Returns:
            Fort16: Contents of the fort.16 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.16 does not exist
        """
        return Fort16.read(directory=self.working_dir)

    def read_fort17(self) -> Fort17:
        """Read and parse the fort.17 file from the working directory.

        This is an output file written by SYNSPEC containing continuum data.

        Returns:
            Fort17: Contents of the fort.17 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.17 does not exist
        """
        return Fort17.read(directory=self.working_dir)

    def read_fort19(self) -> Fort19:
        """Read and parse the fort.19 file from the working directory.

        Returns:
            Fort19: Contents of the fort.19 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.19 does not exist
        """
        return Fort19.read(directory=self.working_dir)

    def write_fort19(self, data: Fort19) -> None:
        """Write data to fort.19 in the working directory.

        Args:
            data: Fort19 instance to write

        Raises:
            RuntimeError: If session is not initialized
            OSError: If writing fails
        """
        data.write(directory=self.working_dir)

    def read_fort55(self) -> Fort55:
        """Read and parse the fort.55 file from the working directory.

        Returns:
            Fort55: Contents of the fort.55 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.55 does not exist
        """
        return Fort55.read(directory=self.working_dir)

    def write_fort55(self, data: Fort55) -> None:
        """Write data to fort.55 in the working directory.

        Args:
            data: Fort55 instance to write

        Raises:
            RuntimeError: If session is not initialized
            OSError: If writing fails
        """
        data.write(directory=self.working_dir)

    def read_fort56(self) -> Fort56:
        """Read and parse the fort.56 file from the working directory.

        Returns:
            Fort56: Contents of the fort.56 file

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.56 does not exist
        """
        return Fort56.read(directory=self.working_dir)

    def write_fort56(self, data: Fort56) -> None:
        """Write data to fort.56 in the working directory.

        Args:
            data: Fort56 instance to write

        Raises:
            RuntimeError: If session is not initialized
            OSError: If writing fails
        """
        data.write(directory=self.working_dir)

    def read_spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        """Read the computed spectrum from fort.7.

        Returns:
            Tuple of (wavelengths, fluxes) arrays

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.7 does not exist
        """
        fort7 = self.read_fort7()
        return fort7.wavelength, fort7.flux

    def read_continuum(self) -> tuple[np.ndarray, np.ndarray]:
        """Read the continuum data from fort.17.

        Returns:
            Tuple of (wavelengths, continuum fluxes) arrays

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.17 does not exist
        """
        fort17 = self.read_fort17()
        return fort17.wavelength, fort17.flux

    def read_normalized_spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        """Read the normalized spectrum from fort.7.

        This normalizes the fluxes by the continuum values.

        Returns:
            Tuple of (wavelengths, normalized fluxes) arrays

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If fort.7 or fort.17 does not exist
        """
        wavelengths, fluxes = self.read_spectrum()
        cont_wavelength, continuum_fluxes = self.read_continuum()
        cont_on_fluxbase = np.interp(wavelengths, cont_wavelength, continuum_fluxes)
        normalized_fluxes = fluxes / cont_on_fluxbase
        return wavelengths, normalized_fluxes

    def compute_equivalent_width(self, wl0: float, wl1: float) -> float:
        """Compute the equivalent width of the spectrum between two wavelengths.

        This uses the normalized spectrum to calculate the equivalent width.

        Args:
            wl0: Start wavelength
            wl1: End wavelength

        Returns:
            float: Equivalent width in Angstroms
        """
        wavelengths, normalized_fluxes = self.read_normalized_spectrum()
        if wl0 < wavelengths[0] or wl1 > wavelengths[-1]:
            raise ValueError("Wavelength range is outside the spectrum limits.")
        mask = (wavelengths >= wl0) & (wavelengths <= wl1)
        if not np.any(mask):
            raise ValueError("Wavelength range is outside the spectrum limits.")
        equivalent_width: float = np.trapz(
            1 - normalized_fluxes[mask], wavelengths[mask]
        )
        return equivalent_width

    def init(self) -> None:
        """Initialize the SYNSPEC session.

        This method is called automatically when using the context manager,
        but can be called manually for longer-running sessions.

        Raises:
            ValueError: If model parameter is missing but {model} placeholders are used
        """
        if not self._working_dir:
            self._working_dir = WorkingDirectory(self.config.working_dir_config)
            self._working_dir.path

    def cleanup(self) -> None:
        """Clean up the session resources."""
        if self._working_dir:
            self._working_dir.cleanup()
            self._working_dir = None

    def __enter__(self) -> Self:
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
        3. Copies/links input files if specified in the configuration
        4. Runs the SYNSPEC executable with the provided model
        5. Collects output files based on configuration, defaulting to synspec outputs
        6. Redirects stdout to a log file (*.log)

        Args:
            model: Base name of the model files (without extension)

        Raises:
            RuntimeError: If session is not initialized
            FileNotFoundError: If required model files are missing
        """
        if self.config.model_dir:
            model_atm = self.config.model_dir / f"{model}.7"
            model_input = self.config.model_dir / f"{model}.5"
        else:
            model_atm = Path(f"{model}.7")
            model_input = Path(f"{model}.5")

        self._prepare_working_directory(model, model_atm)

        self._validate_working_dir(model)

        # Run SYNSPEC with stdin from model.5 and stdout to model.log
        executor = SynspecExecutor(
            config=self.config.execution_config,
            working_dir=self.working_dir,
        )

        executor.execute(
            stdin_file=model_input,
            stdout_file=Path(f"{model}.log"),
        )

        # Collect output files
        self._collect_output_files(model)
