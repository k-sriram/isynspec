"""Tests for SYNSPEC execution strategy."""

import sys
import tempfile
from pathlib import Path

import pytest

from isynspec.io.execution import (
    EXPECTED_OUTPUT_FILES,
    ExecutionConfig,
    ExecutionStrategy,
    FileManagementConfig,
    Shell,
    SynspecExecutor,
)
from isynspec.io.workdir import WorkingDirectory, WorkingDirStrategy


def test_default_execution_config():
    """Test default execution configuration."""
    config = ExecutionConfig()
    assert config.strategy == ExecutionStrategy.SYNSPEC
    assert config.custom_executable is None
    assert config.script_path is None
    assert config.shell == Shell.AUTO
    assert config.file_management.copy_input_files is True
    assert config.file_management.copy_output_files is False
    assert config.file_management.output_directory is None


def test_file_management_config():
    """Test file management configuration."""
    with WorkingDirectory(strategy=WorkingDirStrategy.TEMPORARY) as wd:
        output_dir = wd.path / "output"
        config = ExecutionConfig(
            working_dir=wd,
            file_management=FileManagementConfig(
                copy_input_files=True,
                copy_output_files=True,
                output_directory=output_dir,
                input_files=[Path("input.dat")],
                output_files=[Path("output.dat")],
            ),
        )
        assert config.file_management.copy_input_files is True
        assert config.file_management.copy_output_files is True
        assert config.file_management.output_directory == output_dir
        assert config.file_management.input_files is not None
        assert config.file_management.output_files is not None
        assert config.file_management.input_files[0] == Path("input.dat")
        assert config.file_management.output_files[0] == Path("output.dat")


def test_invalid_execution_config():
    """Test validation of execution configuration."""
    # Test missing custom executable
    with WorkingDirectory(strategy=WorkingDirStrategy.TEMPORARY) as wd:

        with pytest.raises(ValueError, match="must provide custom_executable"):
            ExecutionConfig(working_dir=wd, strategy=ExecutionStrategy.CUSTOM)

        # Test missing script path
        with pytest.raises(ValueError, match="must provide script_path"):
            ExecutionConfig(working_dir=wd, strategy=ExecutionStrategy.SCRIPT)

        # Test missing output directory
        with pytest.raises(ValueError, match="must provide output_directory"):
            ExecutionConfig(
                working_dir=wd,
                file_management=FileManagementConfig(copy_output_files=True),
            )


@pytest.mark.parametrize(
    "shell,expected",
    [
        (Shell.CMD, (["cmd", "/c"], True)),
        (Shell.POWERSHELL, (["powershell", "-Command"], False)),
        (Shell.PWSH, (["pwsh", "-Command"], False)),
        (Shell.BASH, (["bash", "-c"], False)),
        (Shell.SH, (["sh", "-c"], False)),
    ],
)
def test_shell_info(shell, expected):
    """Test shell info for CMD shell."""
    with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
        config = ExecutionConfig(working_dir=wd, shell=shell)
        executor = SynspecExecutor(config)
        cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == expected[0]
    assert use_shell is expected[1]


def test_invalid_shell():
    """Test error on invalid shell type."""
    # Create an invalid shell value
    with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
        config = ExecutionConfig(working_dir=wd, shell=999)  # type: ignore
        executor = SynspecExecutor(config)

    with pytest.raises(ValueError, match="Unknown shell type"):
        executor._get_shell_info()


@pytest.mark.parametrize(
    "shell",
    [
        Shell.CMD,
        Shell.POWERSHELL,
        Shell.PWSH,
        Shell.BASH,
        Shell.SH,
    ],
)
def test_get_command_synspec(shell):
    """Test command generation for SYNSPEC strategy with different shells."""
    with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
        config = ExecutionConfig(
            working_dir=wd,
            strategy=ExecutionStrategy.SYNSPEC,
            shell=shell,
        )
        executor = SynspecExecutor(config)
        cmd = executor._get_command()

    shell_prefix, _ = executor._get_shell_info()
    if len(shell_prefix) > 1:
        assert cmd == shell_prefix + ["synspec"]
    else:
        assert cmd == ["synspec"]


def test_get_command_custom():
    """Test command generation for CUSTOM strategy."""
    with WorkingDirectory(strategy=WorkingDirStrategy.TEMPORARY) as wd:
        exe_path = wd.path / "custom_synspec"
        exe_path.touch(mode=0o755)

        config = ExecutionConfig(
            working_dir=wd,
            strategy=ExecutionStrategy.CUSTOM,
            custom_executable=exe_path,
            shell=Shell.BASH,
        )
        executor = SynspecExecutor(config)
        cmd = executor._get_command()

        assert cmd == ["bash", "-c", str(exe_path)]


def test_get_command_script():
    """Test command generation for SCRIPT strategy."""
    with WorkingDirectory(strategy=WorkingDirStrategy.TEMPORARY) as wd:
        script_path = wd.path / "synspec.py"
        script_path.touch()

        config = ExecutionConfig(
            working_dir=wd,
            strategy=ExecutionStrategy.SCRIPT,
            script_path=script_path,
            shell=Shell.PWSH,
        )
        executor = SynspecExecutor(config)
        cmd = executor._get_command()

        assert cmd == ["pwsh", "-Command", f"python {script_path}"]


def test_get_command_missing_custom():
    """Test error when custom executable is not specified."""
    with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
        config = ExecutionConfig(working_dir=wd, strategy=ExecutionStrategy.CUSTOM)
        executor = SynspecExecutor(config)

        with pytest.raises(ValueError, match="Custom executable not specified"):
            executor._get_command()


def test_get_command_missing_script():
    """Test error when script path is not specified."""
    with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
        config = ExecutionConfig(working_dir=wd, strategy=ExecutionStrategy.SCRIPT)
        executor = SynspecExecutor(config)

        with pytest.raises(ValueError, match="Script path not specified"):
            executor._get_command()


# Start: New test functions for shell detection and command handling
@pytest.mark.skip(reason="Skipping as it requires platform emulation.")
@pytest.mark.parametrize(
    "shell,expected",
    [
        ("win32", Shell.PWSH),
        ("linux", Shell.BASH),
        ("darwin", Shell.BASH),
    ],
)
def test_shell_auto_detection(shell, expected, monkeypatch):
    """Test Shell.AUTO detection based on the current platform."""
    monkeypatch.setattr(sys, "platform", shell)
    assert Shell.detect_default() == expected


def test_path_normalization():
    """Test that paths are properly normalized in commands."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        script_path = (temp_path / ".." / temp_path.name / "script.py").resolve()
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.touch()

        with WorkingDirectory(strategy=WorkingDirStrategy.CURRENT) as wd:
            # Create a configuration with the script path
            config = ExecutionConfig(
                working_dir=wd,
                strategy=ExecutionStrategy.SCRIPT,
                script_path=script_path,
                shell=Shell.BASH,
            )
        executor = SynspecExecutor(config)
        cmd = executor._get_command()

        # Check that the path in the command is normalized
        assert str(script_path.resolve()) in cmd[-1]


# End: New test functions


def test_execution_with_io_redirection(tmp_path, monkeypatch):
    """Test execution with input/output redirection."""
    # Create test input/output paths
    input_file = tmp_path / "input.txt"
    stdout_file = tmp_path / "stdout.txt"
    stderr_file = tmp_path / "stderr.txt"

    # Mock _run_command to verify it's called with correct arguments
    run_command_args: (
        tuple[list[str], Path, bool, Path | None, Path | None, Path | None] | None
    ) = None

    def mock_run_command(
        cmd: list[str],
        working_dir: Path,
        use_shell: bool = False,
        stdin_file: Path | None = None,
        stdout_file: Path | None = None,
        stderr_file: Path | None = None,
    ) -> None:
        nonlocal run_command_args
        run_command_args = (
            cmd,
            working_dir,
            use_shell,
            stdin_file,
            stdout_file,
            stderr_file,
        )
        if stdin_file is not None:
            input_ = stdin_file.read_text()
        else:
            input_ = "default input"
        # Simulate command execution by creating expected output files
        output = f"Received input: {input_}"
        err = "No errors"
        if stdout_file is not None:
            stdout_file.write_text(output)
        else:
            print(output)
        if stderr_file is not None:
            stderr_file.write_text(err)
        else:
            print(err, file=sys.stderr)
        for filename in EXPECTED_OUTPUT_FILES:
            (working_dir / filename).touch()

    monkeypatch.setattr("isynspec.io.execution._run_command", mock_run_command)

    # Create configuration for a SYNSPEC execution
    with WorkingDirectory(strategy=WorkingDirStrategy.SPECIFIED, path=tmp_path) as wd:
        input_file.write_text("Test input data")
        wd.path.mkdir(parents=True, exist_ok=True)
        script_path = wd.path / "synspec"
        script_path.touch()
        config = ExecutionConfig(
            strategy=ExecutionStrategy.SYNSPEC,
            shell=Shell.BASH,  # Use specific shell to make command predictable
            working_dir=wd,
            file_management=FileManagementConfig(
                copy_input_files=False, copy_output_files=False
            ),
        )

        # Create and run executor
        executor = SynspecExecutor(config)
        executor.execute(
            stdin_file=input_file, stdout_file=stdout_file, stderr_file=stderr_file
        )

    # Verify _run_command was called with correct arguments
    assert run_command_args is not None

    # Check command construction
    assert run_command_args[0] == ["bash", "-c", "synspec"]
    assert run_command_args[1] == tmp_path
    assert run_command_args[2] is False
    assert run_command_args[3] == input_file
    assert run_command_args[4] == stdout_file
    assert run_command_args[5] == stderr_file

    # Verify output files were created
    for filename in EXPECTED_OUTPUT_FILES:
        assert (
            tmp_path / filename
        ).exists(), f"Expected output file {filename} not found"

    # Verify stdout and stderr content
    assert stdout_file.read_text() == "Received input: Test input data"
    assert stderr_file.read_text() == "No errors"
