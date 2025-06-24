"""Module for reading SYNSPEC's model input files."""

from dataclasses import dataclass
from typing import Self


@dataclass
class InputData:
    """Data structure for SYNSPEC input file contents."""

    teff: float
    logg: float
    is_lte: bool
    is_ltgray: bool
    nst_filename: str | None

    @classmethod
    def from_file(cls, filepath: str) -> Self:
        """Read SYNSPEC input file and return its contents.

        Args:
            filepath: Path to the input file

        Returns:
            InputData object containing the parsed data
        """
        with open(filepath, "r") as f:
            # Read first line with TEFF and GRAV
            line = f.readline()
            parts = line.strip().split()
            teff = float(parts[0])
            logg = float(parts[1])

            # Read LTE and LTGRAY flags
            line = f.readline()
            parts = line.strip().split()
            is_lte = parts[0].upper() == "T"
            is_ltgray = parts[1].upper() == "T"

            # Read NST filename if present
            line = f.readline().split("!")[0].strip()
            nst_filename = line if line else None

            return cls(
                teff=teff,
                logg=logg,
                is_lte=is_lte,
                is_ltgray=is_ltgray,
                nst_filename=nst_filename,
            )
