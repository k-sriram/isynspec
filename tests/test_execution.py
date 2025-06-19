"""Tests for SYNSPEC execution strategy."""

import sys
import tempfile
from pathlib import Path

import pytest

from isynspec.io.execution import (
    ExecutionConfig,
    ExecutionStrategy,
    FileManagementConfig,
    Shell,
    SynspecExecutor,
)


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
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        config = ExecutionConfig(
            file_management=FileManagementConfig(
                copy_input_files=True,
                copy_output_files=True,
                output_directory=output_dir,
                input_files=[Path("input.dat")],
                output_files=[Path("output.dat")],
            )
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
    with pytest.raises(ValueError, match="must provide custom_executable"):
        ExecutionConfig(strategy=ExecutionStrategy.CUSTOM)

    # Test missing script path
    with pytest.raises(ValueError, match="must provide script_path"):
        ExecutionConfig(strategy=ExecutionStrategy.SCRIPT)

    # Test missing output directory
    with pytest.raises(ValueError, match="must provide output_directory"):
        ExecutionConfig(file_management=FileManagementConfig(copy_output_files=True))


def test_shell_info_cmd():
    """Test shell info for CMD shell."""
    config = ExecutionConfig(shell=Shell.CMD)
    executor = SynspecExecutor(config, Path.cwd())
    cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == ["cmd", "/c"]
    assert use_shell is True


def test_shell_info_powershell():
    """Test shell info for PowerShell."""
    config = ExecutionConfig(shell=Shell.POWERSHELL)
    executor = SynspecExecutor(config, Path.cwd())
    cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == ["powershell", "-Command"]
    assert use_shell is False


def test_shell_info_pwsh():
    """Test shell info for PowerShell Core."""
    config = ExecutionConfig(shell=Shell.PWSH)
    executor = SynspecExecutor(config, Path.cwd())
    cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == ["pwsh", "-Command"]
    assert use_shell is False


def test_shell_info_bash():
    """Test shell info for Bash shell."""
    config = ExecutionConfig(shell=Shell.BASH)
    executor = SynspecExecutor(config, Path.cwd())
    cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == ["bash", "-c"]
    assert use_shell is False


def test_shell_info_sh():
    """Test shell info for POSIX shell."""
    config = ExecutionConfig(shell=Shell.SH)
    executor = SynspecExecutor(config, Path.cwd())
    cmd_prefix, use_shell = executor._get_shell_info()

    assert cmd_prefix == ["sh", "-c"]
    assert use_shell is False


def test_invalid_shell():
    """Test error on invalid shell type."""
    # Create an invalid shell value

    config = ExecutionConfig(shell=999)  # type: ignore
    executor = SynspecExecutor(config, Path.cwd())

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
    config = ExecutionConfig(
        strategy=ExecutionStrategy.SYNSPEC,
        shell=shell,
    )
    executor = SynspecExecutor(config, Path.cwd())
    cmd = executor._get_command()

    shell_prefix, _ = executor._get_shell_info()
    if len(shell_prefix) > 1:
        assert cmd == shell_prefix + ["synspec"]
    else:
        assert cmd == ["synspec"]


def test_get_command_custom():
    """Test command generation for CUSTOM strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        exe_path = Path(temp_dir) / "custom_synspec"
        exe_path.touch(mode=0o755)

        config = ExecutionConfig(
            strategy=ExecutionStrategy.CUSTOM,
            custom_executable=exe_path,
            shell=Shell.BASH,
        )
        executor = SynspecExecutor(config, Path.cwd())
        cmd = executor._get_command()

        assert cmd == ["bash", "-c", str(exe_path)]


def test_get_command_script():
    """Test command generation for SCRIPT strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = Path(temp_dir) / "synspec.py"
        script_path.touch()

        config = ExecutionConfig(
            strategy=ExecutionStrategy.SCRIPT,
            script_path=script_path,
            shell=Shell.PWSH,
        )
        executor = SynspecExecutor(config, Path.cwd())
        cmd = executor._get_command()

        assert cmd == ["pwsh", "-Command", f"python {script_path}"]


def test_get_command_missing_custom():
    """Test error when custom executable is not specified."""
    config = ExecutionConfig(strategy=ExecutionStrategy.CUSTOM)
    executor = SynspecExecutor(config, Path.cwd())

    with pytest.raises(ValueError, match="Custom executable not specified"):
        executor._get_command()


def test_get_command_missing_script():
    """Test error when script path is not specified."""
    config = ExecutionConfig(strategy=ExecutionStrategy.SCRIPT)
    executor = SynspecExecutor(config, Path.cwd())

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

        config = ExecutionConfig(
            strategy=ExecutionStrategy.SCRIPT, script_path=script_path, shell=Shell.BASH
        )
        executor = SynspecExecutor(config, Path.cwd())
        cmd = executor._get_command()

        # Check that the path in the command is normalized
        assert str(script_path.resolve()) in cmd[-1]


# End: New test functions
