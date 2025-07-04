"""Configuration and management of SYNSPEC execution strategies."""

import os
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final, Self, TypeAlias

FileList: TypeAlias = Sequence[Path]
EXPECTED_OUTPUT_FILES: Final[list[str]] = ["fort.7", "fort.17", "fort.16", "fort.12"]


class Shell(StrEnum):
    """Shell to use for execution.

    Attributes:
        AUTO: Automatically detect and use system default shell
        CMD: Windows Command Prompt (cmd.exe)
        POWERSHELL: Windows PowerShell
        PWSH: PowerShell Core (cross-platform)
        BASH: Bash shell
        SH: POSIX shell
    """

    AUTO = "AUTO"
    CMD = "CMD"
    POWERSHELL = "POWERSHELL"
    PWSH = "PWSH"
    BASH = "BASH"
    SH = "SH"

    @classmethod
    def detect_default(cls) -> Self:
        """Detect the default system shell.

        Returns:
            The detected shell type
        """
        if platform.system() == "Windows":
            # Check for PowerShell Core first
            if os.environ.get("PSModulePath", "").lower().find("powershell") >= 0:
                pwsh = subprocess.run(
                    ["pwsh", "-Command", "$PSVersionTable.PSVersion.Major"],
                    capture_output=True,
                    text=True,
                )
                if pwsh.returncode == 0:
                    return cls(cls.PWSH)

            # Then Windows PowerShell
            powershell = subprocess.run(
                ["powershell", "-Command", "$PSVersionTable.PSVersion.Major"],
                capture_output=True,
                text=True,
            )
            if powershell.returncode == 0:
                return cls(cls.POWERSHELL)

            # Fallback to CMD
            return cls(cls.CMD)
        else:
            # On Unix-like systems, check for bash first
            if os.environ.get("SHELL", "").endswith("bash"):
                return cls(cls.BASH)
            # Fallback to sh
            return cls(cls.SH)


class ExecutionStrategy(StrEnum):
    """Strategy for executing SYNSPEC calculations.

    Attributes:
        SYNSPEC: Run the default SYNSPEC executable
        CUSTOM: Run a custom specified executable
        SCRIPT: Run a Python script
    """

    SYNSPEC = "SYNSPEC"
    CUSTOM = "CUSTOM"
    SCRIPT = "SCRIPT"


@dataclass
class FileManagementConfig:
    """Configuration for managing input/output files.

    Attributes:
        copy_input_files: Whether to copy input files to working directory
        copy_output_files: Whether to copy output files back
        output_directory: Directory to copy output files to
        input_files: List of tuples (source_file, renamed_file) for input files.
            If renamed_file is None, the original filename is used.
            If None is provided for the whole list, copy all required files.
        output_files: List of tuples (source_file, renamed_file) for output files.
            If renamed_file is None, the original filename is used.
            If None is provided for the whole list, copy all output files.
        use_symlinks: If True, symlink model.7 to fort.8 instead of copying
    """

    copy_input_files: bool = True
    copy_output_files: bool = False
    output_directory: Path | None = None
    input_files: list[tuple[Path, Path | None]] | None = None
    output_files: list[tuple[Path, Path | None]] | None = None
    use_symlinks: bool = False

    @classmethod
    def from_dict(cls, config_dict: dict) -> Self:
        """Create a FileManagementConfig instance from a dictionary.

        Args:
            config_dict: Dictionary containing configuration options.

        Returns:
            An instance of FileManagementConfig with the provided settings.
        """
        # Handle input files
        input_files: list[tuple[Path, Path | None]] | None = None
        if config_dict.get("input_files"):
            input_files = []
            for file_entry in config_dict["input_files"]:
                if isinstance(file_entry, (str, Path)):
                    input_files.append((Path(file_entry), None))
                else:
                    # Expect a tuple or list with 2 elements
                    source, renamed = file_entry
                    input_files.append(
                        (Path(source), Path(renamed) if renamed is not None else None)
                    )

        # Handle output files
        output_files: list[tuple[Path, Path | None]] | None = None
        if config_dict.get("output_files"):
            output_files = []
            for file_entry in config_dict["output_files"]:
                if isinstance(file_entry, (str, Path)):
                    output_files.append((Path(file_entry), None))
                else:
                    # Expect a tuple or list with 2 elements
                    source, renamed = file_entry
                    output_files.append(
                        (Path(source), Path(renamed) if renamed is not None else None)
                    )

        # Create and return the config instance
        return cls(
            copy_input_files=config_dict.get("copy_input_files", True),
            copy_output_files=config_dict.get("copy_output_files", False),
            output_directory=(
                Path(config_dict.get("output_directory"))  # type: ignore[arg-type]
                if config_dict.get("output_directory")
                else None
            ),
            input_files=input_files,
            output_files=output_files,
            use_symlinks=config_dict.get("use_symlinks", False),
        )


@dataclass
class ExecutionConfig:
    """Configuration for SYNSPEC execution.

    Attributes:
        strategy: The execution strategy to use
        custom_executable: Path to custom executable (when strategy is CUSTOM)
        script_path: Path to Python script (when strategy is SCRIPT)
        working_dir: Working directory configuration
        file_management: Configuration for file management
        shell: Shell to use for execution
    """

    strategy: ExecutionStrategy = ExecutionStrategy.SYNSPEC
    custom_executable: Path | None = None
    script_path: Path | None = None
    file_management: FileManagementConfig = field(default_factory=FileManagementConfig)
    shell: Shell = Shell.AUTO

    def __post_init__(self) -> None:
        """Post-initialization to validate configuration."""
        self.validate_configuration()

    def validate_configuration(self) -> None:
        """Validate configuration."""
        if self.strategy == ExecutionStrategy.CUSTOM and not self.custom_executable:
            raise ValueError("must provide custom_executable with CUSTOM strategy")
        if self.strategy == ExecutionStrategy.SCRIPT and not self.script_path:
            raise ValueError("must provide script_path with SCRIPT strategy")

        if (
            self.file_management.copy_output_files
            and not self.file_management.output_directory
        ):
            msg = "must provide output_directory when copy_output_files is True"
            raise ValueError(msg)

    @classmethod
    def from_dict(cls, config_dict: dict) -> Self:
        """Create an ExecutionConfig instance from a dictionary.

        Args:
            config_dict: Dictionary containing configuration options.

        Returns:
            An instance of ExecutionConfig with the provided settings.
        """
        # In normal usage, these defaults will be overridden by defaults in config.py
        strategy = ExecutionStrategy(config_dict.get("strategy", "SYNSPEC"))
        custom_executable = (
            Path(config_dict["custom_executable"])
            if config_dict.get("custom_executable")
            else None
        )
        script_path = (
            Path(config_dict["script_path"]) if config_dict.get("script_path") else None
        )
        file_management = FileManagementConfig.from_dict(
            config_dict.get("file_management", {})
        )
        shell = Shell(config_dict.get("shell", "AUTO"))

        return cls(
            strategy=strategy,
            custom_executable=custom_executable,
            script_path=script_path,
            file_management=file_management,
            shell=shell,
        )


class ExecutionError(Exception):
    """Raised when SYNSPEC execution fails."""


class SynspecExecutor:
    """Handles execution of SYNSPEC calculations.

    This class runs the configured executable and validates the output.
    """

    def __init__(
        self,
        config: ExecutionConfig,
        working_dir: Path,
    ) -> None:
        """Initialize executor with configuration.

        Args:
            config: Execution configuration
            working_dir: Path to the working directory where execution will occur
        """
        self.config = config
        self.working_dir = working_dir

    def _clean_output_files(self) -> None:
        """Remove any existing output files from working directory."""
        for filename in EXPECTED_OUTPUT_FILES:
            file_path = self.working_dir / filename
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                # If we can't delete a file, just log and continue
                # The execution will fail later if this is a real issue
                pass

    def _validate_output_files(self) -> None:
        """Check that all expected output files were created.

        Raises:
            ExecutionError: If any expected output files are missing
        """
        missing_files = []
        for filename in EXPECTED_OUTPUT_FILES:
            if not (self.working_dir / filename).exists():
                missing_files.append(filename)

        if missing_files:
            missing = ", ".join(missing_files)
            msg = f"SYNSPEC execution failed. Missing output files: {missing}"
            raise ExecutionError(msg)

    def _get_shell_info(self) -> tuple[list[str], bool]:
        """Get shell executable and whether to use shell mode.

        Returns:
            Tuple of (shell command list, use shell mode)
        """
        shell = self.config.shell
        if shell == Shell.AUTO:
            shell = Shell.detect_default()

        if shell == Shell.CMD:
            return ["cmd", "/c"], True  # CMD needs shell mode
        elif shell == Shell.POWERSHELL:
            return ["powershell", "-Command"], False
        elif shell == Shell.PWSH:
            return ["pwsh", "-Command"], False
        elif shell == Shell.BASH:
            return ["bash", "-c"], False
        elif shell == Shell.SH:
            return ["sh", "-c"], False
        else:
            raise ValueError(f"Unknown shell type: {shell}")

    def _get_command(self) -> list[str]:
        """Build the command to execute based on strategy.

        Returns:
            List of command parts to execute
        """
        shell_cmd, _ = self._get_shell_info()

        if self.config.strategy == ExecutionStrategy.CUSTOM:
            if not self.config.custom_executable:
                raise ValueError("Custom executable not specified")
            base_cmd = [str(self.config.custom_executable)]

        elif self.config.strategy == ExecutionStrategy.SCRIPT:
            if not self.config.script_path:
                raise ValueError("Script path not specified")
            # Execute the specified Python script
            script = str(self.config.script_path)
            base_cmd = ["python", script]

        else:  # SYNSPEC strategy
            base_cmd = ["synspec"]

        # For non-shell mode, append the command to the shell invocation
        if len(shell_cmd) > 1:
            # Join the command parts for shell execution
            return shell_cmd + [" ".join(base_cmd)]
        return base_cmd

    def execute(
        self,
        stdin_file: Path | None = None,
        stdout_file: Path | None = None,
        stderr_file: Path | None = None,
    ) -> None:
        """Execute SYNSPEC and validate output.

        This method:
        1. Cleans any existing output files
        2. Runs the configured executable with optional I/O redirection
        3. Validates that all expected output files were created

        Args:
            stdin_file: Optional path to a file to use as standard input
            stdout_file: Optional path to a file to redirect standard output to
            stderr_file: Optional path to a file to redirect standard error to

        Raises:
            ExecutionError: If execution fails or output files are missing
            subprocess.CalledProcessError: If the executable returns non-zero
            OSError: If the executable cannot be run
        """
        # Validate configuration
        self.config.validate_configuration()

        # Clean existing output files
        self._clean_output_files()

        # Build command and get shell mode
        cmd = self._get_command()
        _, use_shell = self._get_shell_info()

        _run_command(
            cmd=cmd,
            working_dir=self.working_dir,
            use_shell=use_shell,
            stdin_file=stdin_file,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )

        # Validate output files
        self._validate_output_files()


def _run_command(
    cmd: list[str],
    working_dir: Path,
    use_shell: bool = False,
    stdin_file: Path | None = None,
    stdout_file: Path | None = None,
    stderr_file: Path | None = None,
) -> None:
    """Run a command in the specified working directory.

    Args:
        cmd: Command to run as a list of arguments
        working_dir: Directory to run the command in
        use_shell: Whether to run the command in shell mode
        stdin_file: Optional file for standard input
        stdout_file: Optional file for standard output
        stderr_file: Optional file for standard error
    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code
        OSError: If the command cannot be executed
    """
    # Prepare file handles for redirection
    stdin = open(stdin_file, "r") if stdin_file else None
    stdout = open(stdout_file, "w") if stdout_file else subprocess.PIPE
    stderr = open(stderr_file, "w") if stderr_file else subprocess.PIPE

    try:
        # Run the command with redirections
        _ = subprocess.run(
            cmd,
            cwd=working_dir,
            shell=use_shell,
            check=True,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        # Include redirected output info in the error message
        if stdout_file:
            stdout_info = f"<redirected to {stdout_file}>"
        else:
            stdout_info = e.stdout or "<no output>"

        if stderr_file:
            stderr_info = f"<redirected to {stderr_file}>"
        else:
            stderr_info = e.stderr or "<no output>"

        raise ExecutionError(
            f"SYNSPEC execution failed with return code {e.returncode}.\n"
            f"stdout: {stdout_info}\nstderr: {stderr_info}"
        ) from e

    except OSError as e:
        raise ExecutionError(f"Failed to run SYNSPEC: {e}") from e

    finally:
        # Clean up file handles
        if stdin is not None:
            stdin.close()
        if not isinstance(stdout, type(subprocess.PIPE)):
            if hasattr(stdout, "close"):
                stdout.close()
        if not isinstance(stderr, type(subprocess.PIPE)):
            if hasattr(stderr, "close"):
                stderr.close()
