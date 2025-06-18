"""Tests for the Fort17 class in isynspec.io.fort17 module."""

import numpy as np
import pytest

from isynspec.io.fort17 import Fort17


@pytest.fixture
def example_data(tmp_path):
    """Create an example fort.17 file with synthetic test data."""
    # Create sample data
    wavelength = np.linspace(300, 700, 100)  # wavelength range 300-700 nm
    # Create a simple absorption-like continuum profile
    continuum = 1 - 0.1 * np.exp(-((wavelength - 500) ** 2) / 1000)

    # Save to temporary file
    file_path = tmp_path / "fort.17"
    np.savetxt(file_path, np.column_stack([wavelength, continuum]))

    return {"file_path": file_path, "wavelength": wavelength, "continuum": continuum}


def test_fort17_creation():
    """Test basic Fort17 object creation."""
    wavelength = np.array([388.0, 388.1, 388.2])
    flux = np.array([1.0, 1.1, 1.2])
    fort17 = Fort17(wavelength=wavelength, flux=flux)
    np.testing.assert_array_equal(fort17.wavelength, wavelength)
    np.testing.assert_array_equal(fort17.flux, flux)


def test_fort17_validation():
    """Test Fort17 validation on creation."""
    wavelength = np.array([388.0, 388.1, 388.2])
    flux = np.array([1.0, 1.1])  # Wrong length
    error_msg = "wavelength and flux arrays must have the same length"
    with pytest.raises(ValueError, match=error_msg):
        Fort17(wavelength=wavelength, flux=flux)


def test_fort17_read(example_data):
    """Test reading a fort.17 file."""
    # Read the file
    fort17 = Fort17.read(example_data["file_path"])

    # Check the data
    np.testing.assert_array_almost_equal(fort17.wavelength, example_data["wavelength"])
    np.testing.assert_array_almost_equal(fort17.flux, example_data["continuum"])


def test_fort17_read_invalid(tmp_path):
    """Test reading an invalid fort.17 file."""
    # Create an invalid test file (wrong number of columns)
    test_file = tmp_path / "fort.17"
    with open(test_file, "w") as f:
        f.write("388.0\n")  # Only one column

    with pytest.raises(TypeError):
        Fort17.read(str(test_file))


def test_fort17_read_nonexistent():
    """Test reading a nonexistent file."""
    with pytest.raises(OSError):
        Fort17.read("nonexistent.dat")
