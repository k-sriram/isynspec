"""Tests for ISynspec session management."""

import tempfile
from pathlib import Path

import platformdirs
import pytest

from isynspec.core.session import ISynspecConfig, ISynspecSession
from isynspec.io.execution import ExecutionConfig, FileManagementConfig
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy


def test_session_initialization():
    """Test basic session initialization."""
    with ISynspecSession() as session:
        assert session.working_dir.exists()
        assert session.working_dir == Path.cwd()  # Default should be current directory


def test_default_config():
    """Test default configuration values."""
    config = ISynspecConfig()
    assert config.working_dir_config.strategy == WorkingDirStrategy.CURRENT


def test_session_with_default_dir():
    """Test session respects default working directory config."""
    config = ISynspecConfig()  # Should use current directory by default
    with ISynspecSession(config) as session:
        assert session.working_dir.exists()
        assert session.working_dir == Path.cwd()


def test_session_with_specified_dir():
    """Test session with specified working directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ISynspecConfig(
            working_dir_config=WorkingDirConfig(
                strategy=WorkingDirStrategy.SPECIFIED, specified_path=temp_dir
            )
        )
        with ISynspecSession(config) as session:
            assert session.working_dir == Path(temp_dir)


def test_session_with_temporary_dir():
    """Test session with temporary directory."""
    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY)
    )
    with ISynspecSession(config) as session:
        temp_dir = session.working_dir
        assert temp_dir.exists()
        assert temp_dir != Path.cwd()
        assert "isynspec_" in temp_dir.name
    # Verify cleanup
    assert not temp_dir.exists()


def test_session_with_user_data_dir():
    """Test session with user data directory."""
    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.USER_DATA)
    )
    with ISynspecSession(config) as session:
        expected_dir = Path(platformdirs.user_data_dir("isynspec"))
        assert session.working_dir == expected_dir
        assert session.working_dir.exists()


def test_manual_session_lifecycle():
    """Test manual initialization and cleanup."""
    session = ISynspecSession()

    # Before initialization
    with pytest.raises(RuntimeError):
        _ = session.working_dir

    # After initialization
    session.init()
    assert session.working_dir.exists()

    # After cleanup
    session.cleanup()
    with pytest.raises(RuntimeError):
        _ = session.working_dir


def test_config_mutable_defaults():
    """Test that mutable defaults in config are handled correctly."""
    config1 = ISynspecConfig()
    config2 = ISynspecConfig()

    # Verify that each instance gets its own copy of working_dir_config
    assert config1.working_dir_config is not config2.working_dir_config

    # Modify one config's working_dir_config
    config1.working_dir_config = WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY)

    # Verify the other config is unchanged
    assert config2.working_dir_config.strategy == WorkingDirStrategy.CURRENT


def test_config_independent_instances():
    """Test that sessions with default configs get independent instances."""
    session1 = ISynspecSession()
    session2 = ISynspecSession()

    # Verify that the configs are independent
    assert session1.config is not session2.config
    assert session1.config.working_dir_config is not session2.config.working_dir_config


def test_file_management_with_model_placeholders(tmp_path: Path):
    """Test file management with {model} placeholders in paths."""
    # Set up test files
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "test_model.dat").write_text("test data")

    output_dir = tmp_path / "output"

    # Configure session with model placeholders
    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY),
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(
                copy_input_files=True,
                copy_output_files=True,
                output_directory=output_dir,
                input_files=[
                    (input_dir / "test_model.dat", Path("{model}.input")),
                ],
                output_files=[
                    (Path("fort.7"), Path("{model}.output")),
                ],
            )
        ),
    )

    # Test with model name
    with ISynspecSession(config=config) as session:
        session._prepare_working_directory(model="mymodel", model_atm=None)

        # Check input file was renamed
        assert (session.working_dir / "mymodel.input").exists()
        assert (session.working_dir / "mymodel.input").read_text() == "test data"

        # Simulate output file creation
        (session.working_dir / "fort.7").write_text("test output")

        session._collect_output_files(model="mymodel")

    # Check output file was collected with model name
    assert output_dir.exists()
    assert (output_dir / "mymodel.output").exists()
    assert (output_dir / "mymodel.output").read_text() == "test output"


def test_default_output_file_mapping(tmp_path: Path):
    """Test default output file mapping when output_files is None."""
    output_dir = tmp_path / "output"

    # Configure session with default output mapping
    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY),
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(
                copy_output_files=True,
                output_directory=output_dir,
                output_files=None,  # Use default mapping
            )
        ),
    )

    with ISynspecSession(config=config) as session:
        # Create mock SYNSPEC output files
        fort_files = {
            "fort.7": "spectrum data",
            "fort.17": "continuum data",
            "fort.12": "identifications",
            "fort.16": "equivalent widths",
        }
        for name, content in fort_files.items():
            (session.working_dir / name).write_text(content)

        # Cleanup with model name
        session._collect_output_files(model="mymodel")

    # Check all default mappings were applied
    expected_files = {
        "mymodel.spec": "spectrum data",
        "mymodel.cont": "continuum data",
        "mymodel.iden": "identifications",
        "mymodel.eqws": "equivalent widths",
    }

    assert output_dir.exists()
    for fname, expected_content in expected_files.items():
        out_file = output_dir / fname
        assert out_file.exists(), f"Missing output file: {fname}"
        assert out_file.read_text() == expected_content


def test_file_management_without_renaming(tmp_path: Path):
    """Test file management when rename paths are None."""
    # Set up test files
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "input.dat").write_text("test data")

    output_dir = tmp_path / "output"

    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY),
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(
                copy_input_files=True,
                copy_output_files=True,
                output_directory=output_dir,
                input_files=[
                    (input_dir / "input.dat", None),  # No renaming
                ],
                output_files=[
                    (Path("output.dat"), None),  # No renaming
                ],
            )
        ),
    )

    with ISynspecSession(config=config) as session:
        session._prepare_working_directory(model="mymodel", model_atm=None)
        # Check input file kept original name
        assert (session.working_dir / "input.dat").exists()
        assert (session.working_dir / "input.dat").read_text() == "test data"

        # Simulate output file creation
        (session.working_dir / "output.dat").write_text("test output")

        session._collect_output_files(model="mymodel")

        # Check output file kept original name
        assert output_dir.exists()
        assert (output_dir / "output.dat").exists()
        assert (output_dir / "output.dat").read_text() == "test output"


def test_file_management_disabled(tmp_path: Path):
    """Test that file management can be disabled."""
    # Set up test files
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "input.dat").write_text("test data")

    output_dir = tmp_path / "output"

    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY),
        execution_config=ExecutionConfig(
            file_management=FileManagementConfig(
                copy_input_files=False,  # Disable input copying
                copy_output_files=False,  # Disable output copying
                output_directory=output_dir,
                input_files=[
                    (input_dir / "input.dat", Path("renamed.dat")),
                ],
                output_files=[
                    (Path("output.dat"), Path("collected.dat")),
                ],
            )
        ),
    )

    with ISynspecSession(config=config) as session:
        session._prepare_working_directory(model="mymodel", model_atm=None)
        # Check no input file was copied
        assert not (session.working_dir / "renamed.dat").exists()
        assert not (session.working_dir / "input.dat").exists()

        # Create output file
        (session.working_dir / "output.dat").write_text("test output")
        session._collect_output_files(model="mymodel")

    # Check no output file was collected
    assert not output_dir.exists()
