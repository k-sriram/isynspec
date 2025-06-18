"""Module for handling SYNSPEC fort.19 line list files.

This module provides functionality for reading and writing SYNSPEC fort.19 files,
which contain spectral line data in the inilin format.
"""

from pathlib import Path
from typing import Self

from isynspec.io.line import Line


class Fort19:
    """Class representing a SYNSPEC fort.19 line list file.

    This class handles reading and writing of fort.19 files which contain
    spectral line data in the inilin format.
    """

    def __init__(self, lines: list[Line]):
        """Initialize a Fort19 instance.

        Args:
            lines: List of Line objects representing the spectral lines
        """
        self.lines = lines

    @classmethod
    def read(cls, directory: Path) -> Self:
        """Create a Fort19 instance by reading from a fort.19 file.

        Args:
            directory: Path to the directory containing the fort.19 file

        Returns:
            Fort19: A new Fort19 instance containing the lines from the file

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file doesn't exist
        """
        file_path = directory / "fort.19"
        lines = []
        with open(file_path, "r") as f:
            lines_iter = iter(f.readlines())
            try:
                while True:
                    lines.append(Line.from_lines_iter(lines_iter))
            except StopIteration:
                pass

        return cls(lines)

    def write(self, directory: Path) -> None:
        """Write the Fort19 instance to a fort.19 file.

        Args:
            directory: Path to the directory where the fort.19 file should be written

        Raises:
            OSError: If the file cannot be written
        """
        with open(directory / "fort.19", "w") as f:
            for line in self.lines:
                f.write(str(line))
