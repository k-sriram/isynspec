"""Tests for fort.16 file reading functionality."""

from pathlib import Path

import numpy as np
import pytest

from isynspec.io.fort16 import Fort16


def test_fort16_read(tmp_path: Path):
    """Test reading a fort.16 file."""
    # Create a sample fort.16 file
    content = r"""
    3947.100    3948.267         0.7         0.7         0.7         0.7
    3948.267    3949.434         0.7         0.7         1.4         1.4
    3949.434    3950.601         0.8         0.8         2.2         2.2
    3950.601    3951.768         1.4         1.4         3.5         3.5
    3951.768    3952.936        58.0        58.0        61.5        61.5
    3952.936    3954.104         1.1         1.1        62.6        62.6
    3954.104    3955.273         1.2         1.2        63.8        63.8
    3955.273    3956.441         1.3         1.3        65.1        65.1
    3956.441    3957.100         0.8         0.8        65.9        65.9
    """

    fort16_path = tmp_path / "fort.16"
    fort16_path.write_text(content)

    # Read the file
    fort16 = Fort16.read(tmp_path)

    # Test array lengths
    assert len(fort16.wave_start) == 9
    assert len(fort16.wave_end) == 9
    assert len(fort16.eqw) == 9
    assert len(fort16.meqw) == 9
    assert len(fort16.cum_eqw) == 9
    assert len(fort16.cum_meqw) == 9

    # Test specific values
    np.testing.assert_almost_equal(fort16.wave_start[0], 3947.100)
    np.testing.assert_almost_equal(fort16.wave_end[0], 3948.267)
    np.testing.assert_almost_equal(fort16.eqw[0], 0.7)
    np.testing.assert_almost_equal(fort16.meqw[0], 0.7)
    np.testing.assert_almost_equal(fort16.cum_eqw[0], 0.7)
    np.testing.assert_almost_equal(fort16.cum_meqw[0], 0.7)

    # Test some middle values
    np.testing.assert_almost_equal(fort16.wave_start[4], 3951.768)
    np.testing.assert_almost_equal(fort16.wave_end[4], 3952.936)
    np.testing.assert_almost_equal(fort16.eqw[4], 58.0)
    np.testing.assert_almost_equal(fort16.meqw[4], 58.0)
    np.testing.assert_almost_equal(fort16.cum_eqw[4], 61.5)
    np.testing.assert_almost_equal(fort16.cum_meqw[4], 61.5)


def test_fort16_invalid_arrays():
    """Test Fort16 initialization with invalid arrays."""
    wave_start = np.array([1.0, 2.0])
    wave_end = np.array([1.5, 2.5])
    eqw = np.array([0.1, 0.2])
    meqw = np.array([0.1])  # Wrong length
    cum_eqw = np.array([0.1, 0.3])
    cum_meqw = np.array([0.1, 0.3])

    with pytest.raises(ValueError, match="All input arrays must have the same length"):
        Fort16(wave_start, wave_end, eqw, meqw, cum_eqw, cum_meqw)


def test_fort16_missing_file(tmp_path: Path):
    """Test attempting to read a non-existent fort.16 file."""
    with pytest.raises(FileNotFoundError):
        Fort16.read(tmp_path)
