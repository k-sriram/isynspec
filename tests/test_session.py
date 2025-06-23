"""Tests for ISynspec session management."""

import tempfile
from pathlib import Path

import pytest

from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy
from isynspec.session import ISynspecConfig, ISynspecSession


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
    import platformdirs

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
