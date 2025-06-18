"""Tests for the Line class in isynspec.io.line module."""

import pytest

from isynspec.io.line import Line


@pytest.fixture
def basic_line():
    """Create a basic Line instance without Stark broadening values."""
    return Line(
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
    )


@pytest.fixture
def stark_line():
    """Create a Line instance with Stark broadening values."""
    return Line(
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
    )


def test_line_creation(basic_line):
    """Test basic Line object creation."""
    assert basic_line.alam == 395.2057
    assert basic_line.anum == 6.01
    assert basic_line.gf == -0.238
    assert basic_line.excl == 195813.660
    assert basic_line.ql == 4.5
    assert basic_line.excu == 221109.780
    assert basic_line.qu == 4.5
    assert basic_line.agam == 8.49
    assert basic_line.gs == -5.12
    assert basic_line.gw == -7.71
    assert basic_line.wgr1 is None
    assert basic_line.ilwn is None


def test_stark_line_creation(stark_line):
    """Test Line object creation with Stark broadening values."""
    assert stark_line.wgr1 == 0.123
    assert stark_line.wgr2 == 0.234
    assert stark_line.wgr3 == 0.345
    assert stark_line.wgr4 == 0.456
    assert stark_line.ilwn == 1
    assert stark_line.iun == 2
    assert stark_line.iprf == 3


def test_has_stark_broadening_values(basic_line, stark_line):
    """Test has_stark_broadening_values method."""
    assert not basic_line.has_stark_broadening_values()
    assert stark_line.has_stark_broadening_values()

    # Test partial values
    partial_line = Line(
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
        wgr1=0.123,  # Only one WGR value
    )
    assert not partial_line.has_stark_broadening_values()


def test_element_code_property(basic_line, stark_line):
    """Test element_code property."""
    assert basic_line.element_code == 6  # Carbon

    line_fe2 = Line(
        alam=400.0,
        anum=26.01,
        gf=0.0,
        excl=0.0,
        ql=0.0,
        excu=0.0,
        qu=0.0,
        agam=0.0,
        gs=0.0,
        gw=0.0,
    )
    assert line_fe2.element_code == 26  # Iron


def test_ionization_property(basic_line, stark_line):
    """Test ionization property."""
    assert basic_line.ionization == 1  # First ionization

    line_fe2 = Line(
        alam=400.0,
        anum=26.01,
        gf=0.0,
        excl=0.0,
        ql=0.0,
        excu=0.0,
        qu=0.0,
        agam=0.0,
        gs=0.0,
        gw=0.0,
    )
    assert line_fe2.ionization == 1  # First ionization

    line_neutral = Line(
        alam=400.0,
        anum=26.00,
        gf=0.0,
        excl=0.0,
        ql=0.0,
        excu=0.0,
        qu=0.0,
        agam=0.0,
        gs=0.0,
        gw=0.0,
    )
    assert line_neutral.ionization == 0  # Neutral


def test_from_lines_iter():
    """Test from_lines_iter class method."""
    # Test basic line
    basic_input = (
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 0"
    )
    lines = iter([basic_input])
    line = Line.from_lines_iter(lines)
    assert line.alam == 395.2057
    assert line.anum == 6.01
    assert not line.has_stark_broadening_values()

    # Test line with Stark broadening
    stark_input = (
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 1"
    )
    lines = iter([stark_input, "0.123 0.234 0.345 0.456 1 2 3"])
    line = Line.from_lines_iter(lines)
    assert line.has_stark_broadening_values()
    assert line.wgr1 == 0.123
    assert line.iprf == 3


def test_from_lines_iter_error_handling():
    """Test error handling in from_lines_iter."""
    # Test invalid format
    with pytest.raises(ValueError, match="Invalid line format"):
        Line.from_lines_iter(iter(["invalid"]))

    # Test missing second line
    input_line = (
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 1"
    )
    with pytest.raises(ValueError, match="Expected second line"):
        Line.from_lines_iter(iter([input_line]))


def test_from_lines():
    """Test from_lines class method."""
    input_lines = [
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 1",
        "0.123 0.234 0.345 0.456 1 2 3",
    ]
    line = Line.from_lines(input_lines)
    assert line.alam == 395.2057
    assert line.has_stark_broadening_values()


def test_from_string():
    """Test from_string class method."""
    # Test basic line
    basic_input = (
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 0\n"
    )
    line = Line.from_string(basic_input)
    assert line.alam == 395.2057
    assert not line.has_stark_broadening_values()

    # Test line with Stark broadening
    stark_input = (
        "  395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    "
        "8.49  -5.12  -7.71 1\n"
        "0.123 0.234 0.345 0.456 1 2 3\n"
    )
    line = Line.from_string(stark_input)
    assert line.has_stark_broadening_values()

    # Test empty string
    with pytest.raises(ValueError, match="Input string is empty"):
        Line.from_string("")


def test_to_lines(basic_line, stark_line):
    """Test to_lines method."""
    # Test basic line
    main_line, next_line = basic_line.to_lines()
    assert "395.2057" in main_line
    assert "6.01" in main_line
    assert main_line.endswith(" 0")
    assert next_line is None

    # Test line with Stark broadening
    main_line, next_line = stark_line.to_lines()
    assert main_line.endswith(" 1")
    assert next_line is not None
    assert "0.123" in next_line
    assert next_line.endswith(" 3")


def test_str_representation(basic_line, stark_line):
    """Test string representation."""
    # Test basic line
    str_basic = str(basic_line)
    assert "395.2057" in str_basic
    assert str_basic.count("\n") == 1

    # Test line with Stark broadening
    str_stark = str(stark_line)
    assert "395.2057" in str_stark
    assert "0.123" in str_stark
    assert str_stark.count("\n") == 2
