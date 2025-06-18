"""Module for handling SYNSPEC fort.19 line list files.

This module provides functionality for reading and writing SYNSPEC fort.19 files,
which contain spectral line data in the inilin format.
"""

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
    def read(cls, file_path: str) -> Self:
        """Create a Fort19 instance by reading from a file.

        Args:
            file_path: Path to the fort.19 file

        Returns:
            Fort19: A new Fort19 instance containing the lines from the file
        """
        lines = []
        with open(file_path, "r") as f:
            lines_iter = iter(f.readlines())
            try:
                while True:
                    lines.append(Line.from_lines_iter(lines_iter))
            except StopIteration:
                pass

        return cls(lines)

    def write(self, file_path: str) -> None:
        """Write the Fort19 instance to a file.

        Args:
            file_path: Path where the fort.19 file should be written
        """
        with open(file_path, "w") as f:
            for line in self.lines:
                f.write(str(line))
