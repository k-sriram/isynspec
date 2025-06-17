"""Tests for Fortran-style I/O utilities."""

import pytest

from isynspec.utils.fortio import (
    FortFloat,
    FortranFormatter,
    FortranReader,
    parse_fortran_float,
    write_fortran_scientific,
)


def test_fortran_number_parse():
    """Test parsing of Fortran-style numbers."""
    # Test standard E notation
    num = FortFloat("1.23E-4")
    assert num.value == pytest.approx(1.23e-4)

    # Test D notation
    num = FortFloat("1.23D-4")
    assert num.value == pytest.approx(1.23e-4)

    # Test implicit exponent
    num = FortFloat("1.23-4")
    assert num.value == pytest.approx(1.23e-4)

    # Test positive exponent with implicit notation
    num = FortFloat("1.23+4")
    assert num.value == pytest.approx(1.23e4)


def test_fortran_number_parse_invalid():
    """Test invalid Fortran number formats."""
    with pytest.raises(ValueError):
        FortFloat("invalid")

    with pytest.raises(ValueError):
        FortFloat("1.23X-4")

    with pytest.raises(ValueError):
        FortFloat("1.23E")


def test_fortran_reader():
    """Test FortranReader field parsing."""
    # Test space-separated fields
    reader = FortranReader("1.0 2.0 3.0")
    fields = list(reader)
    assert fields == ["1.0", "2.0", "3.0"]

    # Test comma-separated fields
    reader = FortranReader("1.0,2.0,3.0")
    fields = list(reader)
    assert fields == ["1.0", "2.0", "3.0"]

    # Test mixed separators
    reader = FortranReader("1.0, 2.0 ,3.0")
    fields = list(reader)
    assert fields == ["1.0", "2.0", "3.0"]

    # Test multiple consecutive separators
    reader = FortranReader("1.0,,,  2.0,   3.0")
    fields = list(reader)
    assert fields == ["1.0", "2.0", "3.0"]

    # Test empty string
    reader = FortranReader("")
    fields = list(reader)
    assert fields == []


def test_parse_fortran_float():
    """Test parse_fortran_float convenience function."""
    assert parse_fortran_float("1.23E-4") == pytest.approx(1.23e-4)
    assert parse_fortran_float("1.23D-4") == pytest.approx(1.23e-4)
    assert parse_fortran_float("1.23-4") == pytest.approx(1.23e-4)


def test_write_fortran_float():
    """Test write_fortran_float formatting."""
    # Test default format
    assert write_fortran_scientific(1.23e-4) == "1.230000E-04"

    # Test with specific width
    assert write_fortran_scientific(1.23e-4, width=12) == " 1.23000E-04"

    # Test with width and decimals
    assert write_fortran_scientific(1.23e-4, width=12, decimals=3) == "   1.230E-04"

    # Test positive exponent
    assert write_fortran_scientific(1.23e4) == "1.230000E+04"

    # Test zero
    assert write_fortran_scientific(0.0) == "0.000000E+00"

    # Test negative number
    assert write_fortran_scientific(-1.23e-4) == "-1.230000E-04"

    # Test force D as exponent
    assert write_fortran_scientific(1.23e-4, double=True) == "1.230000D-04"


def test_fortran_format_format():
    """Test formatting numbers using FortranFormat."""
    # Test F notation
    fmt = FortranFormatter(width=8, decimals=3, notation="F")
    assert fmt.format(123.456) == " 123.456"
    assert fmt.format(-0.789) == "  -0.789"

    # Test F notation without width
    fmt = FortranFormatter(decimals=2, notation="F")
    assert fmt.format(123.456) == "123.46"  # Tests rounding
    assert fmt.format(-0.789) == "-0.79"

    # Test E notation
    fmt = FortranFormatter(width=12, decimals=3, notation="E")
    assert fmt.format(123.456) == "   1.235E+02"
    assert fmt.format(-0.789) == "  -7.890E-01"

    # Test D notation
    fmt = FortranFormatter(width=12, decimals=3, notation="D")
    assert fmt.format(123.456) == "   1.235D+02"
    assert fmt.format(-0.789) == "  -7.890D-01"

    # Test very small numbers
    fmt = FortranFormatter(width=12, decimals=3, notation="E")
    assert fmt.format(1.23e-10) == "   1.230E-10"

    # Test very large numbers
    fmt = FortranFormatter(width=12, decimals=3, notation="E")
    assert fmt.format(1.23e10) == "   1.230E+10"


def test_fortran_format_format_edge_cases():
    """Test edge cases for FortranFormat formatting."""
    # Test zero
    fmt = FortranFormatter(width=8, decimals=3, notation="F")
    assert fmt.format(0.0) == "   0.000"

    # Test integer conversion
    fmt = FortranFormatter(decimals=2, notation="F")
    assert fmt.format(42) == "42.00"

    # Test custom float-like object
    class CustomFloat:
        def __float__(self):
            return 3.14

    fmt = FortranFormatter(width=6, decimals=2, notation="F")
    assert fmt.format(CustomFloat()) == "  3.14"


def test_fortran_format_invalid_inputs():
    """Test invalid inputs for FortranFormat formatting."""
    fmt = FortranFormatter(width=8, decimals=3, notation="F")

    # Test non-numeric input
    with pytest.raises(ValueError):
        fmt.format("not a number")  # type: ignore[arg-type]

    # Test input that doesn't support float conversion
    class NoFloat:
        pass

    with pytest.raises(TypeError):
        fmt.format(NoFloat())  # type: ignore[arg-type]


def test_fortran_format_parse():
    """Test parsing of format specifiers."""
    # Test full format specification (width.decimalsNotation)
    fmt = FortranFormatter.parse("12.3F")
    assert fmt.width == 12
    assert fmt.decimals == 3
    assert fmt.notation == "F"

    # Test format with only width and notation
    fmt = FortranFormatter.parse("12F")
    assert fmt.width == 12
    assert fmt.decimals is None
    assert fmt.notation == "F"

    # Test format with only decimals and notation
    fmt = FortranFormatter.parse(".3E")
    assert fmt.width is None
    assert fmt.decimals == 3
    assert fmt.notation == "E"

    # Test format with only notation
    fmt = FortranFormatter.parse("D")
    assert fmt.width is None
    assert fmt.decimals is None
    assert fmt.notation == "D"

    # Test case insensitivity
    fmt = FortranFormatter.parse("12.3f")
    assert fmt.notation == "F"
    fmt = FortranFormatter.parse("12.3e")
    assert fmt.notation == "E"
    fmt = FortranFormatter.parse("12.3d")
    assert fmt.notation == "D"


def test_fortran_format_parse_invalid():
    """Test parsing of invalid format specifiers."""
    # Test invalid notation
    with pytest.raises(ValueError):
        FortranFormatter.parse("12.3X")

    # Test missing notation
    with pytest.raises(ValueError):
        FortranFormatter.parse("12.3")

    # Test invalid decimal point placement
    with pytest.raises(ValueError):
        FortranFormatter.parse("12..3F")

    # Test invalid width
    with pytest.raises(ValueError):
        FortranFormatter.parse("abc.3F")

    # Test invalid decimals
    with pytest.raises(ValueError):
        FortranFormatter.parse("12.abcF")

    # Test completely invalid format
    with pytest.raises(ValueError):
        FortranFormatter.parse("invalid")
