"""Tests for the fort55 module.

This test suite verifies the functionality of the fort55 module, which handles
SYNSPEC's fort.55 input file configuration.
"""

from pathlib import Path

import pytest

from isynspec.io.fort55 import (
    FILENAME,
    Fort55,
    ModelType,
    OperationMode,
    RadiativeTransferSolver,
)


def test_fort55_config_basic():
    """Test basic Fort55Config initialization with required parameters."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )

    assert config.alam0 == 4000.0
    assert config.alast == 4100.0
    assert config.cutof0 == 0.001
    assert config.relop == 1e-4
    assert config.space == 0.01

    # Check default values
    assert config.imode == OperationMode.NORMAL
    assert config.inmod == ModelType.TLUSTY
    assert config.ifreq == RadiativeTransferSolver.DFE


def test_fort55_config_full():
    """Test Fort55Config initialization with all parameters."""
    config = Fort55(
        alam0=4000.0,
        alast=-4100.0,  # Negative for vacuum wavelengths
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
        imode=OperationMode.MOLECULAR,
        idstd=30,
        iprin=1,
        inmod=ModelType.KURUCZ,
        ifreq=RadiativeTransferSolver.FEAUTRIER,
        vtb=2.0,
        nmu0=3,
        ang0=0.1,
        iflux=1,
        iunitm=[20, 21],  # nmlist will be 2 based on length of iunitm
    )

    # Check custom values
    assert config.alam0 == 4000.0
    assert config.alast == -4100.0
    assert config.imode == OperationMode.MOLECULAR
    assert config.inmod == ModelType.KURUCZ
    assert config.ifreq == RadiativeTransferSolver.FEAUTRIER
    assert config.vtb == 2.0
    assert config.nmu0 == 3
    assert config.ang0 == 0.1
    assert config.iflux == 1
    assert config.iunitm == [20, 21]
    assert config.nmlist == 2


def test_operation_mode_enum():
    """Test OperationMode enumeration values."""
    assert OperationMode.NORMAL == 0
    assert OperationMode.FEW_LINES == 1
    assert OperationMode.CONTINUUM == 2
    assert OperationMode.MOLECULAR == 10
    assert OperationMode.IRON_CURTAIN == -1


def test_model_type_enum():
    """Test ModelType enumeration values."""
    assert ModelType.KURUCZ == 0
    assert ModelType.TLUSTY == 1
    assert ModelType.ACCRETION_DISK == 2


def test_radiative_transfer_solver_enum():
    """Test RadiativeTransferSolver enumeration values."""
    assert RadiativeTransferSolver.DFE == 1
    assert RadiativeTransferSolver.FEAUTRIER == 10


def test_read_write_fort55(tmp_path: Path):
    """Test reading and writing Fort55 configuration to a directory."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
        imode=OperationMode.MOLECULAR,
        idstd=30,
        iprin=1,
        inmod=ModelType.KURUCZ,
        ifreq=RadiativeTransferSolver.FEAUTRIER,
        vtb=2.0,
        nmu0=3,
        ang0=0.1,
        iflux=1,
        iunitm=[20, 21],
    )

    # Write to temporary directory
    config.write(tmp_path)
    assert (tmp_path / FILENAME).exists()

    # Read back and verify
    read_config = Fort55.read(tmp_path)

    # Check all fields match
    assert read_config.alam0 == config.alam0
    assert read_config.alast == config.alast
    assert read_config.cutof0 == config.cutof0
    assert read_config.relop == config.relop
    assert read_config.space == config.space
    assert read_config.imode == config.imode
    assert read_config.idstd == config.idstd
    assert read_config.iprin == config.iprin
    assert read_config.inmod == config.inmod
    assert read_config.ifreq == config.ifreq
    assert read_config.vtb == pytest.approx(config.vtb)
    assert read_config.nmu0 == config.nmu0
    assert read_config.ang0 == pytest.approx(config.ang0)
    assert read_config.iflux == config.iflux
    assert read_config.iunitm == config.iunitm


def test_fort55_invalid_format(tmp_path: Path):
    """Test error handling for invalid fort.55 file format."""
    (tmp_path / FILENAME).write_text("invalid content")

    with pytest.raises(ValueError, match="Invalid fort.55 file format"):
        Fort55.read(tmp_path)


def test_fort55_file_not_found(tmp_path: Path):
    """Test error handling when fort.55 file does not exist."""
    with pytest.raises(FileNotFoundError):
        Fort55.read(tmp_path)


def test_fort55_invalid_wavelength_range(tmp_path: Path):
    """Test error handling for invalid wavelength range."""
    config = Fort55(
        alam0=4100.0,  # Starting wavelength greater than ending wavelength
        alast=4000.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )

    with pytest.raises(ValueError, match="alam0.*must be less than or equal to.*alast"):
        config.write(tmp_path)


def test_read_fort55(test_data_dir: Path):
    """Test reading a valid fort.55 file."""
    # Use a known valid fort.55 file from test data
    config = Fort55.read(test_data_dir)

    assert config.alam0 == 4000.0
    assert config.alast == 4100.0
    assert config.cutof0 == 0.001
    assert config.relop == 1e-4
    assert config.space == 0.01
    assert config.imode == OperationMode.NORMAL
    assert config.inmod == ModelType.TLUSTY
    assert config.ifreq == RadiativeTransferSolver.DFE
    assert config.vtb is None


def test_fort55_with_default_directory(tmp_path: Path):
    """Test Fort55 initialization with default directory and its usage."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
        directory=tmp_path,
    )

    # Write using default directory
    config.write()
    assert (tmp_path / FILENAME).exists()

    # Read back with explicit directory
    read_config = Fort55.read(directory=tmp_path)
    assert read_config.alam0 == config.alam0
    assert read_config.directory == tmp_path

    # Write to a different directory
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    config.write(directory=other_dir)
    assert (other_dir / FILENAME).exists()


def test_fort55_read_with_path(tmp_path: Path):
    """Test Fort55 reading with explicit path."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )

    file_path = tmp_path / FILENAME
    config.write(tmp_path)

    # Read using path parameter
    read_config = Fort55.read(path=file_path)
    assert read_config.alam0 == config.alam0
    assert read_config.directory is None


def test_fort55_write_no_directory():
    """Test Fort55 write with no directory specified."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )

    with pytest.raises(ValueError, match="No directory specified"):
        config.write()
