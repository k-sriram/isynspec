"""Configuration and management of SYNSPEC execution strategies."""

import os
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Final, Self, TypeAlias

FileList: TypeAlias = Sequence[Path]
EXPECTED_OUTPUT_FILES: Final[list[str]] = ["fort.7", "fort.17", "fort.16", "fort.12"]


class Shell(Enum):
    """Shell to use for execution.

    Attributes:
        AUTO: Automatically detect and use system default shell
        CMD: Windows Command Prompt (cmd.exe)
        POWERSHELL: Windows PowerShell
        PWSH: PowerShell Core (cross-platform)
        BASH: Bash shell
        SH: POSIX shell
    """

    AUTO = auto()
    CMD = auto()
    POWERSHELL = auto()
    PWSH = auto()
    BASH = auto()
    SH = auto()

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


class ExecutionStrategy(Enum):
    """Strategy for executing SYNSPEC calculations.

    Attributes:
        SYNSPEC: Run the default SYNSPEC executable
        CUSTOM: Run a custom specified executable
        SCRIPT: Run a Python script
    """

    SYNSPEC = auto()
    CUSTOM = auto()
    SCRIPT = auto()


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
        script_path: Path to Python script (when strategy is SCRIPT)
        file_management: Configuration for file management
        shell: Shell to use for execution
    """

    strategy: ExecutionStrategy = ExecutionStrategy.SYNSPEC
    custom_executable: Path | None = None
    script_path: Path | None = None
    file_management: FileManagementConfig = field(default_factory=FileManagementConfig)
    shell: Shell = Shell.AUTO

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


class ExecutionError(Exception):
    """Raised when SYNSPEC execution fails."""


class SynspecExecutor:
    """Handles execution of SYNSPEC calculations.

    This class runs the configured executable and validates the output.
    """

    def __init__(self, config: ExecutionConfig, working_dir: Path) -> None:
        """Initialize executor with configuration.

        Args:
            config: Execution configuration
            working_dir: Directory where SYNSPEC will run
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

    def execute(self) -> None:
        """Execute SYNSPEC and validate output.

        This method:
        1. Cleans any existing output files
        2. Runs the configured executable
        3. Validates that all expected output files were created

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

        try:
            subprocess.run(
                cmd,
                cwd=self.working_dir,
                shell=use_shell,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise ExecutionError(
                f"SYNSPEC execution failed with return code {e.returncode}.\n"
                f"stdout: {e.stdout}\nstderr: {e.stderr}"
            ) from e
        except OSError as e:
            raise ExecutionError(f"Failed to run SYNSPEC: {e}") from e

        # Validate output files
        self._validate_output_files()
