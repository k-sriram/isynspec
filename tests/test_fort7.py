"""Tests for the Fort7 class in isynspec.io.fort7 module."""

from pathlib import Path

import numpy as np
import pytest

from isynspec.io.fort7 import Fort7


@pytest.fixture
def example_data(tmp_path: Path):
    """Create an example fort.7 file with synthetic test data."""
    # Create sample data
    wavelength = np.linspace(300, 700, 100)  # wavelength range 300-700 nm
    flux = np.exp(-((wavelength - 500) ** 2) / 1000)  # Gaussian-like spectrum

    # Save to temporary file
    np.savetxt(tmp_path / "fort.7", np.column_stack([wavelength, flux]))

    return {"directory": tmp_path, "wavelength": wavelength, "flux": flux}


def test_fort7_creation():
    """Test basic Fort7 object creation."""
    wavelength = np.array([388.0, 388.1, 388.2])
    flux = np.array([1.0, 1.1, 1.2])
    fort7 = Fort7(wavelength=wavelength, flux=flux)
    np.testing.assert_array_equal(fort7.wavelength, wavelength)
    np.testing.assert_array_equal(fort7.flux, flux)


def test_fort7_validation():
    """Test Fort7 validation on creation."""
    wavelength = np.array([388.0, 388.1, 388.2])
    flux = np.array([1.0, 1.1])  # Wrong length
    error_msg = "wavelength and flux arrays must have the same length"
    with pytest.raises(ValueError, match=error_msg):
        Fort7(wavelength=wavelength, flux=flux)


def test_fort7_read(example_data):
    """Test reading a fort.7 file."""
    # Read the file
    fort7 = Fort7.read(example_data["directory"])

    # Check the data
    np.testing.assert_array_almost_equal(fort7.wavelength, example_data["wavelength"])
    np.testing.assert_array_almost_equal(fort7.flux, example_data["flux"])


def test_fort7_read_invalid(tmp_path: Path):
    """Test reading an invalid fort.7 file."""
    # Create an invalid test file (wrong number of columns)
    with open(tmp_path / "fort.7", "w") as f:
        f.write("388.0\n")  # Only one column

    with pytest.raises(TypeError):
        Fort7.read(tmp_path)


def test_fort7_read_nonexistent():
    """Test reading a non-existent fort.7 file."""
    with pytest.raises(FileNotFoundError):
        Fort7.read(Path("nonexistent_dir"))
