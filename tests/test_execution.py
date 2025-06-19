"""Tests for SYNSPEC execution strategy."""

import tempfile
from pathlib import Path

import pytest

from isynspec.io.execution import (
    ExecutionConfig,
    ExecutionStrategy,
    FileManagementConfig,
)
from isynspec.session import ISynspecConfig, ISynspecSession


def test_default_execution_config():
    """Test default execution configuration."""
    config = ISynspecConfig()
    assert config.execution_config.strategy == ExecutionStrategy.SYNSPEC
    assert config.execution_config.custom_executable is None
    assert config.execution_config.rsynspec_script is None
    assert config.execution_config.file_management.copy_input_files is True
    assert config.execution_config.file_management.copy_output_files is False
    assert config.execution_config.file_management.output_directory is None


def test_file_management():
    """Test file management functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        work_dir = Path(temp_dir) / "work"
        work_dir.mkdir()
        input_file = work_dir / "input.dat"
        input_file.write_text("test input")

        output_dir = Path(temp_dir) / "output"

        config = ISynspecConfig(
            execution_config=ExecutionConfig(
                file_management=FileManagementConfig(
                    copy_input_files=True,
                    copy_output_files=True,
                    output_directory=output_dir,
                    input_files=[Path("input.dat")],
                    output_files=[Path("output.dat")],
                )
            )
        )

        with ISynspecSession(config) as session:
            # Create a test output file
            (session.working_dir / "output.dat").write_text("test output")

        # Check output was copied
        assert (output_dir / "output.dat").exists()
        assert (output_dir / "output.dat").read_text() == "test output"


def test_invalid_execution_config():
    """Test validation of execution configuration."""
    # Test missing custom executable
    with pytest.raises(ValueError):
        ExecutionConfig(strategy=ExecutionStrategy.CUSTOM)

    # Test missing RSynspec script
    with pytest.raises(ValueError):
        ExecutionConfig(strategy=ExecutionStrategy.RSYNSPEC)

    # Test missing output directory
    with pytest.raises(ValueError):
        ExecutionConfig(file_management=FileManagementConfig(copy_output_files=True))
