"""Tests for SYNSPEC input file reader."""

from isynspec.io.input import InputData


def test_read_input(test_data_dir):
    """Test reading a SYNSPEC input file."""
    data = InputData.from_file(test_data_dir / "test_model.5")

    assert data.teff == 31000.0
    assert data.logg == 4.2
    assert data.is_lte is True
    assert data.is_ltgray is True
    assert data.nst_filename == "nst"


def test_read_input_with_custom_nst(tmp_path):
    """Test reading an input file with custom NST filename."""
    test_file = tmp_path / "test.5"
    with open(test_file, "w") as f:
        f.write("31000. 4.2\n")
        f.write("T  T\n")
        f.write("custom.nst\n")

    data = InputData.from_file(test_file)
    assert data.nst_filename == "custom.nst"
