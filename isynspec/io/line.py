"""Handler for SYNSPEC line list entries.

This module implements a class for handling individual spectral line entries
in the SYNSPEC line list format (NEW format).

Reference: SYNSPEC documentation, synspec51.f lines 7660-7703
"""

from dataclasses import dataclass
from typing import Iterator, Self

from isynspec.utils.fortio import FortranReader


@dataclass
class Line:
    """Container for a spectral line entry in SYNSPEC's line list.

    Attributes:
        alam: Wavelength in nanometers
        anum: Element and ion code (e.g., 2.00 = HeI, 26.01 = FeII)
        gf: Log gf value
        excl: Lower level excitation potential (in cm⁻¹)
        ql: Lower level J quantum number
        excu: Upper level excitation potential (in cm⁻¹)
        qu: Upper level J quantum number
        agam: Radiation damping (0 for classical, >0 for specific Gamma(rad))
        gs: Stark broadening (0 for classical, >0 for log gamma(Stark))
        gw: Van der Waals broadening (0 for classical, >0 for log gamma(VdW))
        wgr1: Optional Stark broadening at T=5000K (Å)
        wgr2: Optional Stark broadening at T=10000K (Å)
        wgr3: Optional Stark broadening at T=20000K (Å)
        wgr4: Optional Stark broadening at T=40000K (Å)
        ilwn: NLTE handling (0=LTE, >0=NLTE with level index, -1/-2=approx NLTE)
        iun: Upper level population (0=LTE, >0=level index)
        iprf: Stark broadening method (0=use GS, <0=use WGR1-4, >0=special)
    """

    # First record parameters
    alam: float  # wavelength in nm
    anum: float  # element and ion code
    gf: float  # log gf
    excl: float  # lower level excitation potential
    ql: float  # lower level J quantum number
    excu: float  # upper level excitation potential
    qu: float  # upper level J quantum number
    agam: float  # radiation damping
    gs: float  # Stark broadening
    gw: float  # Van der Waals broadening

    # Second record parameters (optional)
    wgr1: float | None = None  # Stark broadening at T=5000K
    wgr2: float | None = None  # Stark broadening at T=10000K
    wgr3: float | None = None  # Stark broadening at T=20000K
    wgr4: float | None = None  # Stark broadening at T=40000K

    # Control parameters (optional)
    ilwn: int | None = None  # NLTE handling
    iun: int | None = None  # Upper level population handling
    iprf: int | None = None  # Stark broadening method

    def has_stark_broadening_values(self) -> bool:
        """Check if the line has Stark broadening values.

        Returns:
            True if all WGR1-WGR4 values are present
        """
        return all(x is not None for x in [self.wgr1, self.wgr2, self.wgr3, self.wgr4])

    @property
    def element_code(self) -> int:
        """Get the atomic number of the element.

        Returns:
            The atomic number extracted from anum
        """
        return int(self.anum)

    @property
    def ionization(self) -> int:
        """Get the ionization stage (0=neutral, 1=first ion, etc).

        Returns:
            The ionization stage extracted from anum
        """
        return round((self.anum % 1) * 100)

    @classmethod
    def from_lines_iter(cls, lines: Iterator[str]) -> Self:
        """Read line data from an iterator of fixed-width format strings.

        Args:
            lines: Iterator of strings, will consume 1-2 lines based on inext flag

        Returns:
            New Line instance with parsed data

        Example format:
            395.2057  6.01 -0.238  195813.660 4.5  221109.780 4.5    8.49  -5.12  -7.71
        """
        # Get first line from iterator
        try:
            while True:
                first_line = next(lines)
                # Strip whitespace and check if line is not empty
                if first_line.strip():
                    break

            # Split line into fixed-width fields
            fields = [
                first_line[0:10].strip(),  # alam
                first_line[10:16].strip(),  # anum
                first_line[16:23].strip(),  # gf
                first_line[23:35].strip(),  # excl
                first_line[35:39].strip(),  # ql
                first_line[39:51].strip(),  # excu
                first_line[51:55].strip(),  # qu
                first_line[55:63].strip(),  # agam
                first_line[63:70].strip(),  # gs
                first_line[70:77].strip(),  # gw
            ]
            print(f"Parsed fields: {fields}")
            # Parse fields
            alam = float(fields[0])
            anum = float(fields[1])
            gf = float(fields[2])
            excl = float(fields[3])
            ql = float(fields[4])
            excu = float(fields[5])
            qu = float(fields[6])
            agam = float(fields[7])
            gs = float(fields[8])
            gw = float(fields[9])

            # Create base line instance
            instance = cls(
                alam=alam,
                anum=anum,
                gf=gf,
                excl=excl,
                ql=ql,
                excu=excu,
                qu=qu,
                agam=agam,
                gs=gs,
                gw=gw,
            )

            # Check if there is additional data
            inext = int(first_line[77:].strip() or "0")

            # Parse next line if inext is 1
            if inext == 1:
                try:
                    second_line = next(lines)
                    # Split into fields using FortranReader since it's space-separated
                    fields2 = FortranReader(second_line)

                    # Parse the 4 WGR values and 3 control parameters
                    instance.wgr1 = float(next(fields2))
                    instance.wgr2 = float(next(fields2))
                    instance.wgr3 = float(next(fields2))
                    instance.wgr4 = float(next(fields2))
                    instance.ilwn = int(next(fields2))
                    instance.iun = int(next(fields2))
                    instance.iprf = int(next(fields2))
                except StopIteration:
                    raise ValueError("Expected second line for Stark broadening values")

            return instance

        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid line format: {e}")

    @classmethod
    def from_lines(cls, lines: list[str]) -> Self:
        """Read line data from a list of fixed-width format strings.

        Args:
            lines: List of strings, will consume 1-2 lines based on inext flag
        Returns:
            New Line instance with parsed data
        """
        return cls.from_lines_iter(iter(lines))

    @classmethod
    def from_string(cls, string: str) -> Self:
        """Read line data from a single fixed-width format string.

        Args:
            string: Single string containing the line data
        Returns:
            New Line instance with parsed data
        """
        lines = string.splitlines()
        if not lines:
            raise ValueError("Input string is empty")
        return cls.from_lines(lines)

    def to_lines(self) -> tuple[str, str | None]:
        """Convert line data to fixed-width format string.

        Returns:
            Tuple of (main_line, next_line) where next_line is None if no
            additional data is present
        """
        # Format main line
        main_line = (
            f"{self.alam:10.4f}"
            f"{self.anum:>6.2f}"
            f"{self.gf:7.3f}"
            f"{self.excl:12.3f}"
            f"{self.ql:4.1f}"
            f"{self.excu:12.3f}"
            f"{self.qu:4.1f}"
            f"{self.agam:8.2f}"
            f"{self.gs:7.2f}"
            f"{self.gw:7.2f}"
        )

        # Add inext flag if we have additional data
        if self.has_stark_broadening_values():
            main_line += " 1"
            # Format next line with Stark broadening values and control parameters
            next_line = (
                f"{self.wgr1:6.3f} "
                f"{self.wgr2:6.3f} "
                f"{self.wgr3:6.3f} "
                f"{self.wgr4:6.3f} "
                f"{self.ilwn or 0:2d} "
                f"{self.iun or 0:2d} "
                f"{self.iprf or 0:2d}"
            )
            return main_line, next_line
        else:
            main_line += " 0"
            return main_line, None

    def __str__(self) -> str:
        """String representation of the Line object.

        Returns:
            A formatted string with main line data and optional Stark broadening values.
        """
        main_line, next_line = self.to_lines()
        if next_line:
            return f"{main_line}\n{next_line}\n"
        else:
            return f"{main_line}\n"
