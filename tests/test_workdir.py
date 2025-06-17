"""Tests for working directory management."""

import tempfile
from pathlib import Path

import platformdirs
import pytest

from isynspec.io.workdir import WorkingDirConfig, WorkingDirectory, WorkingDirStrategy


def test_current_working_dir():
    """Test using current working directory strategy."""
    config = WorkingDirConfig(strategy=WorkingDirStrategy.CURRENT)
    with WorkingDirectory(config) as wd:
        assert wd.path == Path.cwd()


def test_specified_working_dir():
    """Test using specified directory strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "synspec"
        config = WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=path
        )
        with WorkingDirectory(config) as wd:
            assert wd.path == path
            assert path.exists()


def test_temporary_working_dir():
    """Test using temporary directory strategy."""
    config = WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY)
    with WorkingDirectory(config) as wd:
        temp_path = wd.path
        assert temp_path.exists()
        assert temp_path.name.startswith("isynspec_")
    assert not temp_path.exists()


def test_preserved_temporary_working_dir():
    """Test temporary directory with preservation."""
    config = WorkingDirConfig(strategy=WorkingDirStrategy.TEMPORARY, preserve_temp=True)
    with WorkingDirectory(config) as wd:
        temp_path = wd.path
        assert temp_path.exists()
    assert temp_path.exists()
    temp_path.rmdir()  # cleanup after test


def test_user_data_working_dir():
    """Test using user data directory strategy."""
    config = WorkingDirConfig(strategy=WorkingDirStrategy.USER_DATA)
    with WorkingDirectory(config) as wd:
        expected_path = Path(platformdirs.user_data_dir("isynspec"))
        assert wd.path == expected_path
        assert expected_path.exists()


def test_specified_path_validation():
    """Test validation of specified path configuration."""
    with pytest.raises(ValueError):
        WorkingDirConfig(strategy=WorkingDirStrategy.SPECIFIED)


def test_string_path_conversion():
    """Test string paths are converted to Path objects."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=str(temp_dir)
        )
        assert isinstance(config.specified_path, Path)
