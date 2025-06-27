"""Tests for spectrum-related methods in ISynspecSession."""

import numpy as np
import pytest

from isynspec.core.session import ISynspecConfig, ISynspecSession
from isynspec.io.workdir import WorkingDirConfig, WorkingDirStrategy


@pytest.fixture
def spectrum_data():
    """Create sample spectrum data."""
    wavelengths = np.array([4000.0, 4001.0, 4002.0, 4003.0, 4004.0])
    fluxes = np.array([1.0, 0.8, 0.6, 0.8, 1.0])
    return wavelengths, fluxes


@pytest.fixture
def continuum_data():
    """Create sample continuum data."""
    wavelengths = np.array([4000.0, 4002.0, 4004.0])
    # Use a quadratic continuum shape
    fluxes = np.array([1.0, 1.2, 1.0])  # Higher in the middle
    return wavelengths, fluxes


@pytest.fixture
def mock_fort7(tmp_path, spectrum_data):
    """Create a mock fort.7 file."""
    wavelengths, fluxes = spectrum_data
    with open(tmp_path / "fort.7", "w") as f:
        for wl, flux in zip(wavelengths, fluxes):
            f.write(f"{wl:.6f} {flux:.6f}\n")
    return tmp_path / "fort.7"


@pytest.fixture
def mock_fort17(tmp_path, continuum_data):
    """Create a mock fort.17 file."""
    wavelengths, fluxes = continuum_data
    with open(tmp_path / "fort.17", "w") as f:
        for wl, flux in zip(wavelengths, fluxes):
            f.write(f"{wl:.6f} {flux:.6f}\n")
    return tmp_path / "fort.17"


def test_read_spectrum(tmp_path, spectrum_data, mock_fort7):
    """Test reading spectrum from fort.7."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        wavelengths, fluxes = session.read_spectrum()
        expected_wavelengths, expected_fluxes = spectrum_data
        np.testing.assert_array_almost_equal(wavelengths, expected_wavelengths)
        np.testing.assert_array_almost_equal(fluxes, expected_fluxes)


def test_read_continuum(tmp_path, continuum_data, mock_fort17):
    """Test reading continuum from fort.17."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        wavelengths, fluxes = session.read_continuum()
        expected_wavelengths, expected_fluxes = continuum_data
        np.testing.assert_array_almost_equal(wavelengths, expected_wavelengths)
        np.testing.assert_array_almost_equal(fluxes, expected_fluxes)


def test_read_normalized_spectrum(
    tmp_path, spectrum_data, continuum_data, mock_fort7, mock_fort17
):
    """Test reading normalized spectrum."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        wavelengths, normalized_fluxes = session.read_normalized_spectrum()

        # Calculate expected normalized fluxes
        spec_wavelengths, spec_fluxes = spectrum_data
        cont_wavelengths, cont_fluxes = continuum_data
        expected_cont = np.interp(spec_wavelengths, cont_wavelengths, cont_fluxes)
        expected_normalized = spec_fluxes / expected_cont

        np.testing.assert_array_almost_equal(wavelengths, spec_wavelengths)
        np.testing.assert_array_almost_equal(normalized_fluxes, expected_normalized)


def test_compute_equivalent_width(tmp_path, mock_fort7, mock_fort17):
    """Test computing equivalent width."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        # Test with a range that should have a known equivalent width
        ew = session.compute_equivalent_width(4000.0, 4004.0)
        # The equivalent width should be positive and finite
        assert ew > 0
        assert np.isfinite(ew)


def test_compute_equivalent_width_invalid_range(tmp_path, mock_fort7, mock_fort17):
    """Test computing equivalent width with invalid wavelength range."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        error_msg = "Wavelength range is outside the spectrum limits"
        # Test range before spectrum start
        with pytest.raises(ValueError, match=error_msg):
            session.compute_equivalent_width(3900.0, 3950.0)

        # Test range after spectrum end
        with pytest.raises(ValueError, match=error_msg):
            session.compute_equivalent_width(4100.0, 4150.0)


def test_session_not_initialized():
    """Test error handling when session is not initialized."""
    session = ISynspecSession()
    with pytest.raises(RuntimeError, match="Session not initialized"):
        session.read_spectrum()
    with pytest.raises(RuntimeError, match="Session not initialized"):
        session.read_continuum()
    with pytest.raises(RuntimeError, match="Session not initialized"):
        session.read_normalized_spectrum()
    with pytest.raises(RuntimeError, match="Session not initialized"):
        session.compute_equivalent_width(4000.0, 4100.0)


def test_missing_files(tmp_path):
    """Test error handling when required files are missing."""
    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        with pytest.raises(FileNotFoundError):
            session.read_spectrum()
        with pytest.raises(FileNotFoundError):
            session.read_continuum()
        with pytest.raises(FileNotFoundError):
            session.read_normalized_spectrum()
        with pytest.raises(FileNotFoundError):
            session.compute_equivalent_width(4000.0, 4100.0)


def test_normalized_spectrum_interpolation(tmp_path):
    """Test that continuum interpolation works correctly in normalized spectrum."""
    # Create spectrum with more points than continuum
    spec_wavelengths = np.linspace(4000.0, 4004.0, 11)  # 11 points
    spec_fluxes = np.ones_like(spec_wavelengths)
    with open(tmp_path / "fort.7", "w") as f:
        for wl, flux in zip(spec_wavelengths, spec_fluxes):
            f.write(f"{wl:.6f} {flux:.6f}\n")

    # Create continuum with fewer points and varying shape
    cont_wavelengths = np.array([4000.0, 4002.0, 4004.0])  # 3 points
    # Create asymmetric continuum shape
    cont_fluxes = np.array([1.5, 2.0, 1.2])  # Higher in middle, asymmetric ends
    with open(tmp_path / "fort.17", "w") as f:
        for wl, flux in zip(cont_wavelengths, cont_fluxes):
            f.write(f"{wl:.6f} {flux:.6f}\n")

    session_config = ISynspecConfig(
        working_dir_config=WorkingDirConfig(
            strategy=WorkingDirStrategy.SPECIFIED, specified_path=tmp_path
        )
    )
    with ISynspecSession(session_config) as session:
        wavelengths, normalized_fluxes = session.read_normalized_spectrum()

        # Check that interpolation produced expected results
        expected_cont = np.interp(spec_wavelengths, cont_wavelengths, cont_fluxes)
        expected_normalized = spec_fluxes / expected_cont

        np.testing.assert_array_almost_equal(wavelengths, spec_wavelengths)
        np.testing.assert_array_almost_equal(normalized_fluxes, expected_normalized)
