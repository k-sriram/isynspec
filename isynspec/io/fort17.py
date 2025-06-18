"""Module for reading SYNSPEC fort.17 continuum flux files.

This module provides functionality for reading SYNSPEC fort.17 files,
which contain continuum flux data.
"""

from pathlib import Path
from typing import Self, TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


class Fort17:
    """Class representing a SYNSPEC fort.17 continuum flux file.

    This class handles reading fort.17 files which contain wavelength and
    continuum flux data.

    Attributes:
        wavelength: Array of wavelengths
        flux: Array of continuum flux values
    """

    def __init__(self, wavelength: FloatArray, flux: FloatArray):
        """Initialize a Fort17 instance.

        Args:
            wavelength: Array of wavelengths
            flux: Array of continuum flux values

        Raises:
            ValueError: If wavelength and flux arrays have different lengths
        """
        if len(wavelength) != len(flux):
            raise ValueError("wavelength and flux arrays must have the same length")
        self.wavelength = wavelength
        self.flux = flux

    @classmethod
    def read(cls, directory: Path) -> Self:
        """Create a Fort17 instance by reading from a fort.17 file.

        Args:
            directory: Path to the directory containing the fort.17 file

        Returns:
            Fort17: A new Fort17 instance containing the wavelength and flux data

        Raises:
            ValueError: If the file doesn't contain valid data or has wrong format
            FileNotFoundError: If the file doesn't exist
        """
        file_path = directory / "fort.17"
        try:
            data = np.loadtxt(file_path, unpack=True)
            if len(data) != 2:
                raise ValueError("Expected exactly 2 columns (wavelength and flux)")
            return cls(wavelength=data[0], flux=data[1])
        except ValueError as e:
            raise ValueError(f"Invalid fort.17 file format: {e}")
        except OSError as e:
            raise FileNotFoundError(f"Could not read file {file_path}: {e}")
