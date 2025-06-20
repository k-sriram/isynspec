"""Tests for working directory management."""

import tempfile
from pathlib import Path

import platformdirs
import pytest

from isynspec.io.workdir import WorkingDirectory, WorkingDirStrategy


def test_current_working_dir():
    """Test using current working directory strategy."""
    with WorkingDirectory(WorkingDirStrategy.CURRENT) as wd:
        assert wd.path == Path.cwd()


def test_specified_working_dir():
    """Test using specified directory strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "synspec"
        with WorkingDirectory(WorkingDirStrategy.SPECIFIED, path) as wd:
            assert wd.path == path
            assert path.exists()


def test_temporary_working_dir():
    """Test using temporary directory strategy."""
    with WorkingDirectory(WorkingDirStrategy.TEMPORARY) as wd:
        temp_path = wd.path
        assert temp_path.exists()
        assert temp_path.name.startswith("isynspec_")
    assert not temp_path.exists()


def test_preserved_temporary_working_dir():
    """Test temporary directory with preservation."""
    with WorkingDirectory(WorkingDirStrategy.TEMPORARY, preserve_temp=True) as wd:
        temp_path = wd.path
        assert temp_path.exists()
    assert temp_path.exists()
    temp_path.rmdir()  # cleanup after test


def test_user_data_working_dir():
    """Test using user data directory strategy."""
    with WorkingDirectory(WorkingDirStrategy.USER_DATA) as wd:
        expected_path = Path(platformdirs.user_data_dir("isynspec"))
        assert wd.path == expected_path
        assert expected_path.exists()


def test_specified_path_validation():
    """Test validation of specified path configuration."""
    with pytest.raises(ValueError):
        WorkingDirectory(WorkingDirStrategy.SPECIFIED)
