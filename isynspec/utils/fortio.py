"""Utility module for handling Fortran-style I/O.

This module provides utilities for parsing Fortran-style numbers and handling
whitespace/comma-separated fields.
"""

import re
from dataclasses import dataclass
from typing import Self, runtime_checkable

from typing_extensions import Protocol


@runtime_checkable
class SupportsFloat(Protocol):
    """Protocol for objects that can be converted to float."""

    def __float__(self) -> float:
        """Convert to float."""
        ...


@dataclass
class FortranFormatter:
    """Format specifier for Fortran-style numbers."""

    width: int | None = None  # Total field width
    decimals: int | None = None  # Number of decimal places
    notation: str = "F"  # E, D, or F notation

    def __str__(self) -> str:
        """Convert to string representation."""
        parts = []
        if self.width is not None:
            parts.append(str(self.width))
        if self.decimals is not None:
            parts.append("." + str(self.decimals))
        parts.append(self.notation)
        return "".join(parts)

    def format(self, value: SupportsFloat) -> str:
        """Format a value according to this format specifier.

        Args:
            value: The value to format (must support float conversion)

        Returns:
            Formatted string representation
        """
        if not isinstance(value, float) and isinstance(value, SupportsFloat):
            value = float(value)
        if self.notation == "F":
            # Fortran F notation is not scientific, just fixed-point
            if self.width is None:
                return f"{value:.{self.decimals}f}"
            else:
                return f"{value:>{self.width}.{self.decimals}f}"
        return write_fortran_scientific(
            value, self.width, self.decimals, self.notation == "D"
        )

    @classmethod
    def parse(cls, spec: str) -> Self:
        """Parse a format specifier string.

        Examples:
            '12.3D' -> width=12, decimals=3, notation='D'
            '.3E' -> width=None, decimals=3, notation='E'
            '12D' -> width=12, decimals=None, notation='D'
            'F' -> width=None, decimals=None, notation='F'

        Args:
            spec: Format specifier string

        Returns:
            FortranFormat object
        """
        match = re.match(r"^(\d+)?(?:\.(\d+))?([DEF])$", spec.upper())
        if not match:
            raise ValueError(f"Invalid format specifier: {spec}")
        width_str, decimals_str, notation = match.groups()
        width = int(width_str) if width_str else None
        decimals = int(decimals_str) if decimals_str else None
        return cls(width=width, decimals=decimals, notation=notation)


class FortFloat:
    """Container for Fortran-style number parsing results."""

    def __init__(self, value: str | SupportsFloat):
        """Initialize with a Fortran-style number."""
        if isinstance(value, str):
            self.value = FortFloat.parse(value)
        else:
            self.value = float(value)

    @staticmethod
    def parse(text: str) -> float:
        """Parse a Fortran-style number.

        In Fortran, scientific notation can be written in multiple ways:
        - Standard E notation: 1.23E-4
        - D notation: 1.23D-4
        - Implicit exponent: 1.23-4

        Args:
            text: The string to parse

        Returns:
            FortranNumber containing the parsed value and original text

        Raises:
            ValueError: If the text cannot be parsed as a Fortran number
        """
        original = text.strip()
        text = original.upper()

        # Handle standard E notation
        try:
            return float(text)
        except ValueError:
            pass

        # Handle D notation by converting to E notation
        if "D" in text:
            try:
                e_text = text.replace("D", "E")
                return float(e_text)
            except ValueError:
                pass

        # Handle implicit exponent notation (no E/D)
        # Pattern matches: digits[.digits][-+]digits
        pattern = r"^(-?\d*\.?\d+)([-+]\d+)$"
        match = re.match(pattern, text)
        if match:
            mantissa, exponent = match.groups()
            try:
                # Reconstruct as E notation
                e_text = f"{mantissa}E{exponent}"
                return float(e_text)
            except ValueError:
                pass

        raise ValueError(f"Could not parse Fortran number: {text}")

    def __float__(self) -> float:
        """Convert to float."""
        return self.value

    def __format__(self, fspec: str) -> str:
        """Format the number according to a format specifier.

        Args:
            fspec: Format specifier string (like '12.3D') or FortranFormat object

        Returns:
            Formatted string representation
        """
        formatter = FortranFormatter.parse(fspec)
        return formatter.format(self.value)


def parse_fortran_float(text: str) -> float:
    """Parse a Fortran-style float number.

    This is a convenience function that returns just the float value.
    For access to the original text representation, use FortranNumber.parse().

    Args:
        text: The string to parse

    Returns:
        The parsed float value

    Raises:
        ValueError: If the text cannot be parsed as a Fortran number
    """
    return float(FortFloat(text))


def write_fortran_scientific(
    value: float,
    width: int | None = None,
    decimals: int | None = None,
    double: bool = False,
) -> str:
    """Format a float in Fortran-style scientific notation.

    Args:
        value: The value to format
        width: Optional total field width
        decimals: Optional number of decimal places

    Returns:
        The formatted string
    """
    if width is None:
        # Default format: use E notation, 2 digits for exponent
        formatted = f"{value:E}"
    else:
        if decimals is None:
            decimals = width - 7  # Standard Fortran default: width includes 'E±nn'
            if decimals < 0:
                decimals = 0

        # Fortran-style format with D for exponent
        formatted = f"{value:{width}.{decimals}E}"

    if double:
        # Use D notation for double precision
        formatted = formatted.replace("E", "D")

    # Ensure the field width by padding with spaces
    if width is not None:
        formatted = formatted.rjust(width)
    return formatted


class FortranReader:
    """Iterator that reads Fortran-style fields from a string.

    Fields are separated by whitespace or commas. Multiple consecutive
    separators are treated as one.
    """

    def __init__(self, text: str):
        """Initialize the reader.

        Args:
            text: The string to read fields from
        """
        self.text = text.strip()
        self.pos = 0

    def __iter__(self) -> Self:
        """Return self as iterator."""
        return self

    def __next__(self) -> str:
        """Get the next field.

        Returns:
            The next field from the input

        Raises:
            StopIteration: When there are no more fields
        """
        if self.pos >= len(self.text):
            raise StopIteration

        # Skip leading separators
        while self.pos < len(self.text) and (
            self.text[self.pos].isspace() or self.text[self.pos] == ","
        ):
            self.pos += 1

        if self.pos >= len(self.text):
            raise StopIteration

        start = self.pos

        # Read until next separator or end
        while self.pos < len(self.text) and not (
            self.text[self.pos].isspace() or self.text[self.pos] == ","
        ):
            self.pos += 1

        return self.text[start : self.pos]
