"""Tests for the fort55 module.

This test suite verifies the functionality of the fort55 module, which handles
SYNSPEC's fort.55 input file configuration.
"""

import tempfile
from pathlib import Path

import pytest

from isynspec.io.fort55 import Fort55, ModelType, OperationMode, RadiativeTransferSolver


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
        iunitm=[20, 21],
        nmlist=2,
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


def test_write_fort55():
    """Test writing Fort55Config to a file."""
    config = Fort55(
        alam0=4000.0,
        alast=4100.0,
        cutof0=0.001,
        relop=1e-4,
        space=0.01,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "fort.55"
        config.write(path)
        assert path.exists()
        with (
            open(path, "r") as f1,
            open(Path(__file__).parent / "examples" / "example_fort.55", "r") as f2,
        ):
            assert f1.read() == f2.read()


def test_invalid_wavelength_range():
    """Test that starting wavelength must be less than ending wavelength."""
    with pytest.raises(ValueError):
        Fort55(
            alam0=4100.0,  # Greater than alast
            alast=4000.0,
            cutof0=0.001,
            relop=1e-4,
            space=0.01,
        )


def test_invalid_molecular_config():
    """Test validation of molecular line list configuration."""
    with pytest.raises(ValueError):
        Fort55(
            alam0=4000.0,
            alast=4100.0,
            cutof0=0.001,
            relop=1e-4,
            space=0.01,
            nmlist=2,  # Specified 2 lists
            iunitm=[20],  # But only provided 1 unit number
        )


def test_invalid_ang0_without_vtb():
    """Test that setting ang0 without vtb raises an error."""
    with pytest.raises(ValueError, match="ang0 cannot be set without setting vtb"):
        Fort55(
            alam0=4000.0,
            alast=4100.0,
            cutof0=0.001,
            relop=1e-4,
            space=0.01,
            ang0=0.1,  # Setting ang0 without vtb should raise an error
        )


def test_read_fort55():
    """Test reading fort.55 configuration from a file."""
    example_path = Path(__file__).parent / "examples" / "example_fort.55"
    config = Fort55.read(example_path)

    # First row: 0 32 0 (imode, idstd, iprin)
    assert config.imode == OperationMode.NORMAL
    assert config.idstd == 32
    assert config.iprin == 0

    # Second row: 1 0 0 0 (inmod, intrpl, ichang, ichemc)
    assert config.inmod == ModelType.TLUSTY
    assert config.intrpl == 0
    assert config.ichang == 0
    assert config.ichemc == 0

    # Third row: 0 0 0 0 0 (iophli, nunalp, nunbet, nungam, nunbal)
    assert config.iophli == 0
    assert config.nunalp == 0
    assert config.nunbet == 0
    assert config.nungam == 0
    assert config.nunbal == 0

    # Fourth row: 1 0 0 0 0 (ifreq, inlte, icontl, inlist, ifhe2)
    assert config.ifreq == RadiativeTransferSolver.DFE
    assert config.inlte == 0
    assert config.icontl == 0
    assert config.inlist == 0
    assert config.ifhe2 == 0

    # Fifth row: 0 0 0 (ihydpr, ihe1pr, ihe2pr)
    assert config.ihydpr == 0
    assert config.ihe1pr == 0
    assert config.ihe2pr == 0

    # Sixth row: 4000.0 4100.0 0.001 0.0 0.0001 0.01
    assert config.alam0 == 4000.0
    assert config.alast == 4100.0
    assert config.cutof0 == 0.001
    assert config.cutofs == 0.0
    assert config.relop == 0.0001
    assert config.space == 0.01

    # Seventh row: 0 0i (nmlist and iunitm)
    assert config.nmlist == 0
    assert config.iunitm == []

    # Optional parameters should be at their default values
    assert config.vtb is None
    assert config.nmu0 == 0
    assert config.ang0 is None
    assert config.iflux == 0
