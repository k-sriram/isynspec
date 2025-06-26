"""Module for handling SYNSPEC fort.19 line list files.

This module provides functionality for reading and writing SYNSPEC fort.19 files,
which contain spectral line data in the inilin format.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from isynspec.io.line import Line


@dataclass
class Fort19:
    """Class representing a SYNSPEC fort.19 line list file.

    This class handles reading and writing of fort.19 files which contain
    spectral line data in the inilin format.

    Attributes:
        lines: List of Line objects representing the spectral lines
        directory: Default directory to write to and read from.
                  If None, must be specified in read/write calls.
    """

    lines: list[Line]
    directory: Path | None = None  # Default directory for read/write operations

    @classmethod
    def read(cls, directory: Path | None = None, *, path: Path | None = None) -> Self:
        """Create a Fort19 instance by reading from a fort.19 file.

        Args:
            directory: Directory containing fort.19 file.
                      If None and path is None, raises ValueError.
            path: Complete path to the fort.19 file.
                 If provided, directory is ignored.

        Returns:
            Fort19: A new Fort19 instance containing the lines from the file

        Raises:
            ValueError: If the file format is invalid or no path is specified
            FileNotFoundError: If the file doesn't exist
        """
        if path is None:
            if directory is None:
                raise ValueError("Either directory or path must be specified")
            path = path = Path(directory) / "fort.19"

        lines = []
        with open(path, "r") as f:
            lines_iter = iter(f.readlines())
            try:
                while True:
                    lines.append(Line.from_lines_iter(lines_iter))
            except StopIteration:
                pass

        fort19 = cls(lines=lines)
        # Set the directory if one was provided
        if directory is not None:
            fort19.directory = directory
        return fort19

    def write(self, directory: Path | None = None) -> None:
        """Write the Fort19 instance to a fort.19 file.

        Args:
            directory: Directory where to write the fort.19 file.
                      If None, uses the default directory set during initialization.

        Raises:
            ValueError: If no directory is specified
            OSError: If the file cannot be written
        """
        if directory is None:
            if self.directory is None:
                raise ValueError("No directory specified for writing fort.19")
            directory = self.directory

        with open(directory / "fort.19", "w") as f:
            for line in self.lines:
                f.write(str(line))
