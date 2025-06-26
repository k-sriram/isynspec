"""Tests for file access methods in ISynspecSession."""

import pytest

from isynspec.core.session import ISynspecConfig, ISynspecSession
from isynspec.io.fort19 import Fort19
from isynspec.io.fort55 import Fort55
from isynspec.io.fort56 import Fort56
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy


@pytest.fixture
def session():
    """Create a test session with a temporary working directory."""
    config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY)
    )
    with ISynspecSession(config=config) as sess:
        sess.init()
        yield sess


def test_uninitialized_session():
    """Test that file operations fail on uninitialized session."""
    session = ISynspecSession()
    with pytest.raises(RuntimeError, match="Session not initialized"):
        session.read_fort55()


def test_read_missing_file(session):
    """Test that reading missing files raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        session.read_fort55()


def test_write_fort55(session, tmp_path):
    """Test writing and reading fort.55."""
    # Create test data and write it
    data = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )
    session.write_fort55(data)

    # Read it back
    read_data = session.read_fort55()
    assert isinstance(read_data, Fort55)


def test_write_fort56(session, tmp_path):
    """Test writing and reading fort.56."""
    # Create test data and write it
    data = Fort56(changes=[])
    session.write_fort56(data)

    # Read it back
    read_data = session.read_fort56()
    assert isinstance(read_data, Fort56)


def test_write_fort19(session, tmp_path):
    """Test writing and reading fort.19."""
    # Create test data and write it
    data = Fort19(lines=[])
    session.write_fort19(data)

    # Read it back
    read_data = session.read_fort19()
    assert isinstance(read_data, Fort19)
    assert read_data.lines == []
