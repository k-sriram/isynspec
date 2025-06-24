"""Test configuration and fixtures."""

import sys
from pathlib import Path

import pytest

from isynspec.io.execution import EXPECTED_OUTPUT_FILES


@pytest.fixture
def mock_run_command(monkeypatch):
    """Mock the _run_command function in SynspecExecutor.

    This fixture provides a way to simulate SYNSPEC execution without requiring
    the actual executable. It creates the expected output files and provides
    access to the arguments that were passed to the command.

    Returns:
        function: A function that returns the arguments of the last command execution
    """
    run_command_args = None

    def _mock_run_command(
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
        # Simulate command execution by creating expected output files
        if stdin_file is not None:
            input_ = stdin_file.read_text()
        else:
            input_ = "default input"

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

        # Create the expected output files
        for filename in EXPECTED_OUTPUT_FILES:
            (working_dir / filename).touch()

    monkeypatch.setattr("isynspec.io.execution._run_command", _mock_run_command)
    return lambda: run_command_args


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "data"
