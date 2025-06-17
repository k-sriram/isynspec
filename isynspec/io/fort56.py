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


@dataclass
class AtomicAbundance:
    """Container for atomic abundance change."""

    atomic_number: int  # Atomic number of the element
    abundance: float  # New abundance value


@dataclass
class Fort56:
    """Container for SYNSPEC fort.56 input file.

    This file specifies changes to chemical abundances in the model atmosphere.
    """

    changes: list[AtomicAbundance]  # List of abundance changes

    @classmethod
    def read(cls, path: str | Path) -> Self:
        """Read fort.56 file and create Fort56 instance.

        Args:
            path: Path to fort.56 file

        Returns:
            New Fort56 instance with parsed data
        """
        path = Path(path)
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

            return cls(changes=changes)

        except (ValueError, IndexError, StopIteration) as e:
            raise ValueError(f"Invalid fort.56 file format: {e}")

    def write(self, path: str | Path) -> None:
        """Write Fort56 data to file.

        Args:
            path: Path where to write the fort.56 file
        """
        path = Path(path)

        with path.open("w") as f:
            # Write number of changes
            f.write(f"{len(self.changes):5d}\n")

            # Write each abundance change
            for change in self.changes:
                f.write(f"{change.atomic_number:>3d} {change.abundance:.3E}\n")
