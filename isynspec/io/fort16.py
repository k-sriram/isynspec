"""Module for reading SYNSPEC fort.16 equivalent width files.

This module provides functionality for reading SYNSPEC fort.16 files,
which contain equivalent width data in wavelength bins.
"""

from pathlib import Path
from typing import Self, TypeAlias

import numpy as np
from numpy.typing import NDArray

FloatArray: TypeAlias = NDArray[np.float64]


class Fort16:
    """Class representing a SYNSPEC fort.16 equivalent width file.

    This class handles reading fort.16 files which contain wavelength intervals
    and their corresponding equivalent width data.

    Attributes:
        wave_start: Array of initial wavelengths for each interval
        wave_end: Array of final wavelengths for each interval
        eqw: Array of equivalent widths
        meqw: Array of modified equivalent widths (emission features cut off)
        cum_eqw: Array of cumulative equivalent widths
        cum_meqw: Array of cumulative modified equivalent widths
    """

    def __init__(
        self,
        wave_start: FloatArray,
        wave_end: FloatArray,
        eqw: FloatArray,
        meqw: FloatArray,
        cum_eqw: FloatArray,
        cum_meqw: FloatArray,
    ):
        """Initialize a Fort16 instance.

        Args:
            wave_start: Array of initial wavelengths for each interval
            wave_end: Array of final wavelengths for each interval
            eqw: Array of equivalent widths
            meqw: Array of modified equivalent widths
            cum_eqw: Array of cumulative equivalent widths
            cum_meqw: Array of cumulative modified equivalent widths

        Raises:
            ValueError: If arrays have different lengths
        """
        arrays = [wave_start, wave_end, eqw, meqw, cum_eqw, cum_meqw]
        if not all(len(arr) == len(wave_start) for arr in arrays):
            raise ValueError("All input arrays must have the same length")

        self.wave_start = wave_start
        self.wave_end = wave_end
        self.eqw = eqw
        self.meqw = meqw
        self.cum_eqw = cum_eqw
        self.cum_meqw = cum_meqw

    @classmethod
    def read(cls, directory: Path) -> Self:
        """Create a Fort16 instance by reading from a fort.16 file.

        Args:
            directory: Path to the directory containing the fort.16 file

        Returns:
            Fort16: A new Fort16 instance with wavelength and equivalent width data

        Raises:
            FileNotFoundError: If fort.16 file is not found in the directory
        """
        file_path = directory / "fort.16"
        if not file_path.exists():
            raise FileNotFoundError(f"fort.16 file not found in {directory}")

        # Load all data from the file
        data = np.loadtxt(file_path)

        # Extract columns
        wave_start = data[:, 0]
        wave_end = data[:, 1]
        eqw = data[:, 2]
        meqw = data[:, 3]
        cum_eqw = data[:, 4]
        cum_meqw = data[:, 5]

        return cls(wave_start, wave_end, eqw, meqw, cum_eqw, cum_meqw)
