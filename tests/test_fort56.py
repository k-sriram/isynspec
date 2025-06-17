"""Tests for the fort56 module.

This test suite verifies the functionality of the fort56 module, which handles
SYNSPEC's fort.56 input file for atomic abundance changes.
"""

import tempfile
from pathlib import Path

import pytest

from isynspec.io.fort56 import AtomicAbundance, Fort56


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


def test_fort56_read_write():
    """Test reading and writing Fort56 data to a file."""
    # Create test data
    original_changes = [
        AtomicAbundance(atomic_number=26, abundance=7.5),
        AtomicAbundance(atomic_number=6, abundance=8.2),
        AtomicAbundance(atomic_number=8, abundance=8.7),
    ]
    fort56 = Fort56(changes=original_changes)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        fort56.write(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        # Read back and verify
        read_fort56 = Fort56.read(tmp_path)

        assert len(read_fort56.changes) == len(original_changes)
        for orig, read in zip(original_changes, read_fort56.changes):
            assert orig.atomic_number == read.atomic_number
            assert orig.abundance == pytest.approx(read.abundance)

    finally:
        # Cleanup
        tmp_path.unlink()


def test_fort56_invalid_format():
    """Test error handling for invalid fort.56 file format."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write("invalid content")
        tmp_path = Path(tmp.name)

    try:
        with pytest.raises(ValueError, match="Invalid fort.56 file format"):
            Fort56.read(tmp_path)

    finally:
        # Cleanup
        tmp_path.unlink()


def test_fort56_empty_changes():
    """Test Fort56 with empty changes list."""
    fort56 = Fort56(changes=[])

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        fort56.write(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        # Read back and verify
        read_fort56 = Fort56.read(tmp_path)
        assert len(read_fort56.changes) == 0

    finally:
        # Cleanup
        tmp_path.unlink()
