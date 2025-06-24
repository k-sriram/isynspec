"""Tests for ISynspecSession configuration and execution."""

import os
from pathlib import Path

import pytest

from isynspec.core.session import ISynspecConfig, ISynspecSession
from isynspec.io.execution import ExecutionConfig, FileManagementConfig


def test_model_dir_config(tmp_path: Path, test_data_dir: Path, mock_run_command):
    """Test that model_dir configuration works correctly."""
    # Copy test files to a separate model directory
    model_dir = tmp_path / "models"
    model_dir.mkdir()

    # Copy test files
    for ext in [".5", ".7"]:
        src = test_data_dir / f"test_model{ext}"
        dst = model_dir / f"test_model{ext}"
        dst.write_bytes(src.read_bytes())

    # Create config with model_dir
    config = ISynspecConfig(model_dir=model_dir)

    with ISynspecSession(config=config) as session:
        # This should succeed since files are in model_dir
        session.run("test_model")

        # Check that fort.8 was created and contains correct content
        fort8 = session.working_dir / "fort.8"
        assert fort8.exists()
        assert fort8.read_bytes() == (model_dir / "test_model.7").read_bytes()

        # Verify SynspecExecutor was called with correct arguments
        cmd_args = mock_run_command()
        assert cmd_args is not None
        assert cmd_args[3] == model_dir / "test_model.5"  # stdin_file
        assert cmd_args[4].name == "test_model.log"  # stdout_file


def test_model_dir_not_found(tmp_path: Path):
    """Test that appropriate error is raised when model files don't exist."""
    config = ISynspecConfig(model_dir=tmp_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        with ISynspecSession(config=config) as session:
            session.run("nonexistent_model")

    assert "Model atmosphere file not found" in str(exc_info.value)


@pytest.mark.skipif(os.name == "nt", reason="Symlinks not supported on Windows")
def test_use_symlinks(tmp_path: Path, test_data_dir: Path, mock_run_command):
    """Test that use_symlinks option creates symbolic links instead of copying."""
    # Copy test files to working directory
    for ext in [".5", ".7"]:
        src = test_data_dir / f"test_model{ext}"
        dst = tmp_path / f"test_model{ext}"
        dst.write_bytes(src.read_bytes())

    # Create config with use_symlinks=True
    config = ISynspecConfig(
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(use_symlinks=True)
        )
    )

    with ISynspecSession(config=config) as session:
        session.run("test_model")

        # Check that fort.8 is a symlink to the model file
        fort8 = session.working_dir / "fort.8"
        assert fort8.is_symlink()
        assert os.path.realpath(fort8) == os.path.realpath(tmp_path / "test_model.7")

        # Verify SynspecExecutor was called correctly
        cmd_args = mock_run_command()
        assert cmd_args is not None
        assert cmd_args[3] == tmp_path / "test_model.5"  # stdin_file
        assert cmd_args[4].name == "test_model.log"  # stdout_file


@pytest.mark.skipif(os.name == "nt", reason="Symlinks not supported on Windows")
def test_model_dir_with_symlinks(tmp_path: Path, test_data_dir: Path):
    """Test that model_dir and use_symlinks work together correctly."""
    # Set up model directory
    model_dir = tmp_path / "models"
    model_dir.mkdir()

    # Copy test files to model directory
    for ext in [".5", ".7"]:
        src = test_data_dir / f"test_model{ext}"
        dst = model_dir / f"test_model{ext}"
        dst.write_bytes(src.read_bytes())

    # Create config with both model_dir and use_symlinks
    config = ISynspecConfig(
        model_dir=model_dir,
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(use_symlinks=True)
        ),
    )

    with ISynspecSession(config=config) as session:
        session.run("test_model")

        # Check that fort.8 is a symlink to the model file in model_dir
        fort8 = session.working_dir / "fort.8"
        assert fort8.is_symlink()
        assert os.path.realpath(fort8) == os.path.realpath(model_dir / "test_model.7")


@pytest.mark.skipif(os.name == "nt", reason="Symlinks not supported on Windows")
def test_symlink_cleanup(tmp_path: Path, test_data_dir: Path, mock_run_command):
    """Test that symlinks are properly cleaned up when session ends."""
    # Copy test files
    for ext in [".5", ".7"]:
        src = test_data_dir / f"test_model{ext}"
        dst = tmp_path / f"test_model{ext}"
        dst.write_bytes(src.read_bytes())

    config = ISynspecConfig(
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(use_symlinks=True)
        )
    )

    with ISynspecSession(config=config) as session:
        session.run("test_model")
        fort8 = session.working_dir / "fort.8"
        assert fort8.exists()

    # After session ends, fort.8 should be gone
    assert not fort8.exists()


def test_existing_fort8_replacement(
    tmp_path: Path, test_data_dir: Path, mock_run_command
):
    """Test that existing fort.8 is properly replaced."""
    # Copy test files
    for ext in [".5", ".7"]:
        src = test_data_dir / f"test_model{ext}"
        dst = tmp_path / f"test_model{ext}"
        dst.write_bytes(src.read_bytes())

    # Create an existing fort.8
    (tmp_path / "fort.8").write_text("existing file")

    config_dict = {
        "model_dir": tmp_path,
        "working_dir": {"strategy": "TEMPORARY"},
    }

    # Test with copying
    config1 = ISynspecConfig.from_dict(config_dict)
    with ISynspecSession(config=config1) as session:
        session.run("test_model")
        fort8 = session.working_dir / "fort.8"
        assert fort8.exists()
        assert not fort8.is_symlink()
        assert fort8.read_bytes() == (tmp_path / "test_model.7").read_bytes()

        # Verify SynspecExecutor was called correctly
        cmd_args = mock_run_command()
        assert cmd_args is not None
        assert cmd_args[3] == tmp_path / "test_model.5"  # stdin_file
        assert cmd_args[4].name == "test_model.log"  # stdout_file

    if os.name == "nt":
        # On Windows, we don't support symlinks, so we skip the next part
        return

    config_dict = {
        "model_dir": tmp_path,
        "working_dir": {"strategy": "TEMPORARY"},
        "execution": {"file_management": {"use_symlinks": True}},
    }

    # Recreate fort.8 and test with symlinks
    (tmp_path / "fort.8").write_text("existing file")
    config2 = ISynspecConfig(
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(use_symlinks=True)
        )
    )
    with ISynspecSession(config=config2) as session:
        session.run("test_model")
        fort8 = session.working_dir / "fort.8"
        assert fort8.exists()
        assert fort8.is_symlink()
        assert os.path.realpath(fort8) == os.path.realpath(tmp_path / "test_model.7")

        # Verify SynspecExecutor was called correctly
        cmd_args = mock_run_command()
        assert cmd_args is not None
        assert cmd_args[3] == tmp_path / "test_model.5"  # stdin_file
        assert cmd_args[4].name == "test_model.log"  # stdout_file
