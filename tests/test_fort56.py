"""Tests for the fort56 module.

This test suite verifies the functionality of the fort56 module, which handles
SYNSPEC's fort.56 input file for atomic abundance changes.
"""

from pathlib import Path

import pytest

from isynspec.io.fort56 import FILENAME, AtomicAbundance, Fort56


def test_atomic_abundance_basic():
    """Test basic AtomicAbundance initialization."""
    abundance = AtomicAbundance(atomic_number=26, abundance=7.5)
    assert abundance.atomic_number == 26
    assert abundance.abundance == 7.5


def test_fort56_basic():
    """Test basic Fort56 initialization with a list of abundance changes."""
    changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),
        AtomicAbundance(atomic_number=6, abundance=8.2),
    ]
    fort56 = Fort56(changes=changes)

    assert len(fort56.changes) == 2
    assert fort56.changes[0].atomic_number == 26
    assert fort56.changes[0].abundance == 7.5
    assert fort56.changes[1].atomic_number == 6
    assert fort56.changes[1].abundance == 8.2


def test_fort56_read_write(tmp_path: Path):
    """Test reading and writing Fort56 data to a directory."""
    # Create test data
    original_changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),
        AtomicAbundance(atomic_number=6, abundance=8.2),
        AtomicAbundance(atomic_number=8, abundance=8.7),
    ]
    fort56 = Fort56(changes=original_changes)

    # Write to temporary directory
    fort56.write(tmp_path)
    assert (tmp_path / FILENAME).exists()

    # Read back and verify
    read_fort56 = Fort56.read(tmp_path)

    assert len(read_fort56.changes) == len(original_changes)
    for orig, read in zip(original_changes, read_fort56.changes):
        assert orig.atomic_number == read.atomic_number
        assert orig.abundance == pytest.approx(read.abundance)


def test_fort56_invalid_format(tmp_path: Path):
    """Test error handling for invalid fort.56 file format."""
    # Create invalid fort.56 file
    (tmp_path / FILENAME).write_text("invalid content")

    with pytest.raises(ValueError, match="Invalid fort.56 file format"):
        Fort56.read(tmp_path)


def test_fort56_empty_changes(tmp_path: Path):
    """Test Fort56 with empty changes list."""
    fort56 = Fort56(changes=[])

    # Write to temporary directory
    fort56.write(tmp_path)
    assert (tmp_path / FILENAME).exists()

    # Read back and verify
    read_fort56 = Fort56.read(tmp_path)
    assert len(read_fort56.changes) == 0


def test_fort56_file_not_found(tmp_path: Path):
    """Test error handling when fort.56 file does not exist."""
    with pytest.raises(FileNotFoundError):
        Fort56.read(tmp_path)


def test_fort56_with_default_directory(tmp_path: Path):
    """Test Fort56 initialization with default directory and its usage."""
    changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),
        AtomicAbundance(atomic_number=6, abundance=8.2),
    ]
    fort56 = Fort56(changes=changes, directory=tmp_path)

    # Write using default directory
    fort56.write()
    assert (tmp_path / FILENAME).exists()

    # Read back with explicit directory
    read_fort56 = Fort56.read(directory=tmp_path)
    assert len(read_fort56.changes) == len(fort56.changes)
    assert read_fort56.directory == tmp_path

    # Write to a different directory
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    fort56.write(directory=other_dir)
    assert (other_dir / FILENAME).exists()


def test_fort56_read_with_path(tmp_path: Path):
    """Test Fort56 reading with explicit path."""
    changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),
        AtomicAbundance(atomic_number=6, abundance=8.2),
    ]
    fort56 = Fort56(changes=changes)

    file_path = tmp_path / FILENAME
    fort56.write(tmp_path)

    # Read using path parameter
    read_fort56 = Fort56.read(path=file_path)
    assert len(read_fort56.changes) == len(fort56.changes)
    assert read_fort56.directory is None


def test_fort56_write_no_directory():
    """Test Fort56 write with no directory specified."""
    changes = [AtomicAbundance(atomic_number=26, abundance=7.5)]
    fort56 = Fort56(changes=changes)

    with pytest.raises(ValueError, match="No directory specified"):
        fort56.write()


def test_fort56_as_tuples():
    """Test the as_tuples property."""
    # Create a Fort56 instance with multiple changes
    changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),  # Iron
        AtomicAbundance(atomic_number=6, abundance=8.4),  # Carbon
        AtomicAbundance(atomic_number=8, abundance=8.7),  # Oxygen
    ]
    fort56 = Fort56(changes=changes)

    # Get the tuples
    tuples = fort56.as_tuples

    # Verify the tuples match the original data
    assert len(tuples) == len(changes)
    for (atomic_number, abundance), change in zip(tuples, changes):
        assert atomic_number == change.atomic_number
        assert abundance == change.abundance

    # Verify the order is preserved
    assert tuples == [(26, 7.5), (6, 8.4), (8, 8.7)]


def test_fort56_from_tuples():
    """Test creating Fort56 from tuples."""
    # Test with valid data
    tuples = [(26, 7.5), (6, 8.4), (8, 8.7)]
    fort56 = Fort56.from_tuples(tuples)
    assert len(fort56.changes) == 3
    assert fort56.changes[0].atomic_number == 26
    assert fort56.changes[0].abundance == 7.5
    assert fort56.changes[1].atomic_number == 6
    assert fort56.changes[1].abundance == 8.4
    assert fort56.changes[2].atomic_number == 8
    assert fort56.changes[2].abundance == 8.7

    # Test with empty list
    fort56 = Fort56.from_tuples([])
    assert len(fort56.changes) == 0

    # Test with invalid atomic numbers
    with pytest.raises(ValueError, match="Atomic number must be a positive integer"):
        Fort56.from_tuples([(0, 7.5)])
    with pytest.raises(ValueError, match="Atomic number must be a positive integer"):
        Fort56.from_tuples([(-1, 7.5)])

    # Test with directory
    directory = Path("test/dir")
    fort56 = Fort56.from_tuples(tuples, directory=directory)
    assert fort56.directory == directory
