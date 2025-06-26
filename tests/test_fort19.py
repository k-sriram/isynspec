"""Tests for the Fort19 class in isynspec.io.fort19 module."""

import pytest

from isynspec.io.fort19 import Fort19
from isynspec.io.line import Line


@pytest.fixture
def basic_lines():
    """Create a list of basic Line instances."""
    return [
        Line(
            alam=395.2057,
            anum=6.01,
            gf=-0.238,
            excl=195813.660,
            ql=4.5,
            excu=221109.780,
            qu=4.5,
            agam=8.49,
            gs=-5.12,
            gw=-7.71,
        ),
        Line(
            alam=396.1057,
            anum=7.01,
            gf=-0.338,
            excl=195813.660,
            ql=4.5,
            excu=221109.780,
            qu=4.5,
            agam=8.49,
            gs=-5.12,
            gw=-7.71,
        ),
    ]


@pytest.fixture
def stark_lines():
    """Create a list of Line instances with Stark broadening values."""
    return [
        Line(
            alam=395.2057,
            anum=6.01,
            gf=-0.238,
            excl=195813.660,
            ql=4.5,
            excu=221109.780,
            qu=4.5,
            agam=8.49,
            gs=-5.12,
            gw=-7.71,
            wgr1=0.123,
            wgr2=0.234,
            wgr3=0.345,
            wgr4=0.456,
            ilwn=1,
            iun=2,
            iprf=3,
        ),
        Line(
            alam=396.1057,
            anum=7.01,
            gf=-0.338,
            excl=195813.660,
            ql=4.5,
            excu=221109.780,
            qu=4.5,
            agam=8.49,
            gs=-5.12,
            gw=-7.71,
            wgr1=0.123,
            wgr2=0.234,
            wgr3=0.345,
            wgr4=0.456,
            ilwn=1,
            iun=2,
            iprf=3,
        ),
    ]


def test_fort19_creation(basic_lines):
    """Test basic Fort19 object creation."""
    fort19 = Fort19(basic_lines)
    assert len(fort19.lines) == 2
    assert isinstance(fort19.lines[0], Line)
    assert fort19.lines[0].alam == 395.2057
    assert fort19.lines[1].alam == 396.1057


def test_fort19_read_write(tmp_path, basic_lines):
    """Test reading and writing fort.19 files."""
    # Create a Fort19 instance
    fort19 = Fort19(basic_lines)

    # Write to temporary directory
    fort19.write(tmp_path)

    # Read it back
    fort19_read = Fort19.read(tmp_path)

    # Compare the lines
    assert len(fort19_read.lines) == len(fort19.lines)
    for line1, line2 in zip(fort19.lines, fort19_read.lines):
        assert line1.alam == line2.alam
        assert line1.anum == line2.anum
        assert line1.gf == line2.gf
        assert line1.excl == line2.excl
        assert line1.ql == line2.ql
        assert line1.excu == line2.excu
        assert line1.qu == line2.qu
        assert line1.agam == line2.agam
        assert line1.gs == line2.gs
        assert line1.gw == line2.gw


def test_fort19_read_write_stark(tmp_path, stark_lines):
    """Test reading and writing fort.19 files with Stark broadening values."""
    # Create a Fort19 instance
    fort19 = Fort19(stark_lines)

    # Write to temporary directory
    fort19.write(tmp_path)

    # Read it back
    fort19_read = Fort19.read(tmp_path)

    # Compare the lines
    assert len(fort19_read.lines) == len(fort19.lines)
    for line1, line2 in zip(fort19.lines, fort19_read.lines):
        assert line1.alam == line2.alam
        assert line1.anum == line2.anum
        assert line1.gf == line2.gf
        assert line1.excl == line2.excl
        assert line1.ql == line2.ql
        assert line1.excu == line2.excu
        assert line1.qu == line2.qu
        assert line1.agam == line2.agam
        assert line1.gs == line2.gs
        assert line1.gw == line2.gw
        assert line1.wgr1 == line2.wgr1
        assert line1.wgr2 == line2.wgr2
        assert line1.wgr3 == line2.wgr3
        assert line1.wgr4 == line2.wgr4
        assert line1.ilwn == line2.ilwn
        assert line1.iun == line2.iun
        assert line1.iprf == line2.iprf


def test_fort19_read(tmp_path):
    """Test reading a real fort.19 file in NEW format."""
    # Create a fort.19 file with real format data
    with open(tmp_path / "fort.19", "w") as f:
        # Example from SYNSPEC documentation, NEW format
        # Values: He I line at 388.8646 nm
        f.write(
            "  388.8646  2.00  1.223  193917.12  2.0  219866.87  3.0  8.72  "
            "-4.51  -7.31  1\n"
        )
        f.write("  0.987  1.234  1.567  1.890  0  0  -1\n")  # Stark broadening data
        # Fe II line without Stark broadening
        f.write(
            "  395.2057 26.01 -0.238  195813.66  4.5  221109.78  4.5  8.49  "
            "-5.12  -7.71\n"
        )

    # Read the directory containing the file
    fort19 = Fort19.read(tmp_path)

    # Check the first line (He I with Stark broadening)
    line1 = fort19.lines[0]
    assert line1.alam == pytest.approx(388.8646)
    assert line1.anum == pytest.approx(2.00)  # He I
    assert line1.gf == pytest.approx(1.223)
    assert line1.excl == pytest.approx(193917.12)
    assert line1.ql == pytest.approx(2.0)
    assert line1.excu == pytest.approx(219866.87)
    assert line1.qu == pytest.approx(3.0)
    assert line1.agam == pytest.approx(8.72)
    assert line1.gs == pytest.approx(-4.51)
    assert line1.gw == pytest.approx(-7.31)
    # Stark broadening parameters
    assert line1.wgr1 == pytest.approx(0.987)
    assert line1.wgr2 == pytest.approx(1.234)
    assert line1.wgr3 == pytest.approx(1.567)
    assert line1.wgr4 == pytest.approx(1.890)
    assert line1.ilwn == 0
    assert line1.iun == 0
    assert line1.iprf == -1

    # Check the second line (Fe II without Stark broadening)
    line2 = fort19.lines[1]
    assert line2.alam == pytest.approx(395.2057)
    assert line2.anum == pytest.approx(26.01)  # Fe II
    assert line2.gf == pytest.approx(-0.238)
    assert line2.excl == pytest.approx(195813.66)
    assert line2.ql == pytest.approx(4.5)
    assert line2.excu == pytest.approx(221109.78)
    assert line2.qu == pytest.approx(4.5)
    assert line2.agam == pytest.approx(8.49)
    assert line2.gs == pytest.approx(-5.12)
    assert line2.gw == pytest.approx(-7.71)
    assert line2.wgr1 is None
    assert line2.wgr2 is None
    assert line2.wgr3 is None
    assert line2.wgr4 is None
    assert line2.ilwn is None
    assert line2.iun is None
    assert line2.iprf is None


def test_fort19_with_default_directory(tmp_path, basic_lines):
    """Test Fort19 initialization with default directory and its usage."""
    fort19 = Fort19(lines=basic_lines, directory=tmp_path)

    # Write using default directory
    fort19.write()
    assert (tmp_path / "fort.19").exists()

    # Read back with explicit directory
    read_fort19 = Fort19.read(directory=tmp_path)
    assert len(read_fort19.lines) == len(fort19.lines)
    assert read_fort19.directory == tmp_path

    # Write to a different directory
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    fort19.write(directory=other_dir)
    assert (other_dir / "fort.19").exists()


def test_fort19_read_with_path(tmp_path, basic_lines):
    """Test Fort19 reading with explicit path."""
    fort19 = Fort19(lines=basic_lines)

    file_path = tmp_path / "fort.19"
    fort19.write(tmp_path)

    # Read using path parameter
    read_fort19 = Fort19.read(path=file_path)
    assert len(read_fort19.lines) == len(fort19.lines)
    assert read_fort19.directory is None


def test_fort19_write_no_directory(basic_lines):
    """Test Fort19 write with no directory specified."""
    fort19 = Fort19(lines=basic_lines)

    with pytest.raises(ValueError, match="No directory specified"):
        fort19.write()
