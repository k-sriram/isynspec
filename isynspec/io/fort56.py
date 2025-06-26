"""Handler for SYNSPEC's fort.56 input file.

The fort.56 file specifies changes to chemical abundances in the model atmosphere.
The file format is: "nchang (iatom abn)x{nchang}" where nchang is the number of
atomic abundance changes, followed by nchang pairs of values where iatom is the
atomic number (integer) and abn is the abundance (float).

Reference: SYNSPEC documentation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

from isynspec.utils.fortio import FortFloat

FILENAME = "fort.56"


@dataclass
class AtomicAbundance:
    """Container for atomic abundance change."""

    atomic_number: int  # Atomic number of the element
    abundance: float  # New abundance value


@dataclass
class Fort56:
    """Container for SYNSPEC fort.56 input file.

    This file specifies changes to chemical abundances in the model atmosphere.

    Attributes:
        changes: List of abundance changes
        directory: Default directory to write to and read from.
                  If None, must be specified in read/write calls.
    """

    changes: list[AtomicAbundance]  # List of abundance changes
    directory: Path | None = None  # Default directory for read/write operations

    @classmethod
    def read(cls, directory: Path | None = None, *, path: Path | None = None) -> Self:
        """Read fort.56 file and create Fort56 instance.

        Args:
            directory: Directory containing fort.56 file.
                      If None and path is None, raises ValueError.
            path: Complete path to the fort.56 file.
                 If provided, directory is ignored.

        Returns:
            New Fort56 instance with parsed data

        Raises:
            ValueError: If the file format is invalid
            FileNotFoundError: If the file does not exist
        """
        if path is None:
            if directory is None:
                raise ValueError("Either directory or path must be specified")
            path = directory / FILENAME

        text = path.read_text()
        fields = text.split()

        try:
            # Get an iterator over the fields
            reader = iter(fields)

            # First read the number of changes
            nchang = int(next(reader))

            changes = []
            # Read nchang pairs of (atomic_number, abundance)
            for _ in range(nchang):
                iatom = int(next(reader))
                abn = float(FortFloat(next(reader)))
                changes.append(AtomicAbundance(atomic_number=iatom, abundance=abn))

            fort56 = cls(changes=changes)
            # Set the directory if one was provided
            if directory is not None:
                fort56.directory = directory
            return fort56

        except (ValueError, IndexError, StopIteration) as e:
            raise ValueError(f"Invalid fort.56 file format: {e}")

    @classmethod
    def from_tuples(
        cls, tuples: list[tuple[int, float]], *, directory: Path | None = None
    ) -> Self:
        """Create a Fort56 instance from a list of (atomic_number, abundance) tuples.

        Args:
            tuples: List of tuples, each containing (atomic_number, abundance)
            directory: Optional directory for read/write operations

        Returns:
            A new Fort56 instance with the specified abundance changes

        Raises:
            ValueError: If any atomic number is not a positive integer
        """
        changes = []
        for atomic_number, abundance in tuples:
            if not isinstance(atomic_number, int) or atomic_number <= 0:
                raise ValueError(
                    f"Atomic number must be a positive integer, got {atomic_number}"
                )
            changes.append(
                AtomicAbundance(atomic_number=atomic_number, abundance=abundance)
            )
        return cls(changes=changes, directory=directory)

    @property
    def as_tuples(self) -> list[tuple[int, float]]:
        """Get the abundance changes as a list of (atomic_number, abundance) tuples.

        Returns:
            List of tuples, each containing (atomic_number, abundance).
            The list is ordered the same as the changes list.
        """
        return [(change.atomic_number, change.abundance) for change in self.changes]

    def write(self, directory: Path | None = None) -> None:
        """Write Fort56 data to file.

        Args:
            directory: Directory where to write the fort.56 file.
                      If None, uses the default directory set during initialization.

        Raises:
            ValueError: If no directory is specified
            OSError: If the file cannot be written
        """
        if directory is None:
            if self.directory is None:
                raise ValueError("No directory specified for writing fort.56")
            directory = self.directory

        path = directory / FILENAME

        with path.open("w") as f:
            # Write number of changes
            f.write(f"{len(self.changes):5d}\n")

            # Write each abundance change
            for change in self.changes:
                f.write(f"{change.atomic_number:>3d} {change.abundance:.3E}\n")
