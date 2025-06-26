"""Handler for SYNSPEC's fort.55 input file.

The fort.55 file controls the main parameters for spectral synthesis in SYNSPEC.
It specifies parameters like wavelength range, line selection criteria, model atmosphere
type, and various physical treatment options.

Reference: SYNSPEC documentation
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Self

from isynspec.utils.fortio import FortFloat, FortranReader

FILENAME = "fort.55"


class OperationMode(IntEnum):
    """Basic mode of operation for SYNSPEC."""

    NORMAL = 0  # Normal synthetic spectrum
    FEW_LINES = 1  # Spectrum for a few lines (obsolete)
    CONTINUUM = 2  # Continuum (plus H and He II lines) only
    MOLECULAR = 10  # Spectrum with molecular lines
    IRON_CURTAIN = -1  # Opacity at standard depth only, no transfer equation


class ModelType(IntEnum):
    """Type of input model atmosphere."""

    KURUCZ = 0  # Kurucz model
    TLUSTY = 1  # TLUSTY model
    ACCRETION_DISK = 2  # Accretion disk model


class RadiativeTransferSolver(IntEnum):
    """Choice of radiative transfer equation solver."""

    DFE = 1  # Default, Discontinuous Finite Element method
    FEAUTRIER = 10  # Feautrier scheme


@dataclass
class Fort55:
    """Container for SYNSPEC fort.55 input file.

    All parameter names match those in SYNSPEC source code for clarity.
    Default values are set for typical use cases.

    Attributes:
        directory: Default directory to write to and read from.
                  If None, must be specified in read/write calls.
    """

    # Wavelength and line selection parameters (required)
    alam0: float  # Starting wavelength [Å]
    alast: float  # Ending wavelength [Å], negative for vacuum wavelengths
    cutof0: float  # Line opacity cutoff [Å] (except H, HeII)
    relop: float  # Line rejection parameter (opacity ratio threshold)
    space: float  # Maximum wavelength spacing [Å]

    # Basic operation parameters
    imode: OperationMode = OperationMode.NORMAL
    idstd: int = 32  # Standard depth index (~2/3 of total depth points)
    iprin: int = 0  # Print detail level (0=normal)

    # Model atmosphere parameters
    inmod: ModelType = ModelType.TLUSTY
    intrpl: int = 0  # Model interpolation flag
    ichang: int = 0  # Model change flag
    ichemc: int = 0  # Chemical composition change flag (needs fort.56)

    # Line treatment parameters
    iophli: int = 0  # Far Lα wings treatment (obsolete)
    nunalp: int = 0  # Lα quasi-molecular satellites
    nunbet: int = 0  # Lβ quasi-molecular satellites
    nungam: int = 0  # Lγ quasi-molecular satellites
    nunbal: int = 0  # Hα quasi-molecular satellites

    # Radiative transfer parameters
    ifreq: RadiativeTransferSolver = RadiativeTransferSolver.DFE
    inlte: int = 0  # LTE treatment flag (1 for NLTE, 0 for forced LTE)
    icontl: int = 0  # Obsolete
    inlist: int = 0  # Obsolete
    ifhe2: int = 0  # HeII hydrogenic treatment

    # Line profile parameters
    ihydpr: int = 0  # Special H line profiles
    ihe1pr: int = 0  # Special HeI line profiles
    ihe2pr: int = 0  # Special HeII line profiles

    # Dummy variables
    cutofs: float = 0.0  # Dummy variable

    # Molecular line parameters
    # Unit numbers for molecular line lists
    iunitm: list[int] = field(default_factory=list)

    # Optional parameters
    vtb: float | None = None  # Microturbulent velocity [km/s]
    nmu0: int = 0  # Number of emission angles
    ang0: float | None = None  # Angle for specific intensity
    iflux: int = 0  # Flux integration flag

    # I/O parameters
    directory: Path | None = None  # Default directory for read/write operations

    @property
    def nmlist(self) -> int:
        """Number of additional molecular line lists."""
        return len(self.iunitm)

    def write(self, directory: Path | None = None) -> None:
        """Write configuration to fort.55 file.

        Args:
            directory: Directory where to write the fort.55 file.
                      If None, uses the default directory set during initialization.

        Raises:
            ValueError: If wavelength range is invalid or no directory is specified
            OSError: If file cannot be written
        """
        if directory is None:
            if self.directory is None:
                raise ValueError("No directory specified for writing fort.55")
            directory = self.directory
        path = directory / FILENAME
        with open(path, "w") as f:
            # Basic operation parameters
            f.write(f"{int(self.imode)} ")
            f.write(f"{self.idstd} ")
            f.write(f"{self.iprin}\n")

            # Model parameters
            f.write(f"{int(self.inmod)} ")
            f.write(f"{self.intrpl} ")
            f.write(f"{self.ichang} ")
            f.write(f"{self.ichemc}\n")

            # Line physics parameters
            f.write(f"{self.iophli} ")
            f.write(f"{self.nunalp} ")
            f.write(f"{self.nunbet} ")
            f.write(f"{self.nungam} ")
            f.write(f"{self.nunbal}\n")

            # More line physics parameters
            f.write(f"{int(self.ifreq)} ")
            f.write(f"{self.inlte} ")
            f.write(f"{self.icontl} ")
            f.write(f"{self.inlist} ")
            f.write(f"{self.ifhe2}\n")

            # Line profile parameters
            f.write(f"{self.ihydpr} ")
            f.write(f"{self.ihe1pr} ")
            f.write(f"{self.ihe2pr}\n")

            # Wavelength parameters - check validity first
            if self.alam0 > abs(self.alast):
                raise ValueError(
                    f"alam0({self.alam0}) must be less than or equal to "
                    f"alast({self.alast})"
                )
            f.write(
                f"{self.alam0} {self.alast} {self.cutof0} {self.cutofs} {self.relop} "
                f"{self.space}\n"
            )

            # Molecular lines
            if self.nmlist > 0:
                units_str = " ".join(str(u) for u in self.iunitm)
                f.write(f"{self.nmlist} {units_str}\n")
            else:
                f.write("0 0i\n")  # Standard placeholder when no molecular lines

            # Optional parameters
            if self.vtb is not None:
                f.write(f"{self.vtb}\n")

            if self.nmu0 > 0:
                f.write(f"{self.nmu0} {self.ang0} {self.iflux}\n")

    @classmethod
    def _read_int_params(
        cls, reader: FortranReader, params: dict[str, int | float | list[int] | None]
    ) -> None:
        """Read integer parameters from the reader."""
        # Basic operation parameters
        params["imode"] = int(next(reader))
        params["idstd"] = int(next(reader))
        params["iprin"] = int(next(reader))

        # Model parameters
        params["inmod"] = int(next(reader))
        params["intrpl"] = int(next(reader))
        params["ichang"] = int(next(reader))
        params["ichemc"] = int(next(reader))

        # Line physics parameters
        params["iophli"] = int(next(reader))
        params["nunalp"] = int(next(reader))
        params["nunbet"] = int(next(reader))
        params["nungam"] = int(next(reader))
        params["nunbal"] = int(next(reader))

        # More line physics parameters
        params["ifreq"] = int(next(reader))
        params["inlte"] = int(next(reader))
        params["icontl"] = int(next(reader))
        params["inlist"] = int(next(reader))
        params["ifhe2"] = int(next(reader))

        # Line profile parameters
        params["ihydpr"] = int(next(reader))
        params["ihe1pr"] = int(next(reader))
        params["ihe2pr"] = int(next(reader))

    @classmethod
    def _read_wavelength_params(
        cls, reader: FortranReader, params: dict[str, int | float | list[int] | None]
    ) -> None:
        """Read wavelength parameters from the reader."""
        params["alam0"] = float(FortFloat(next(reader)).value)
        params["alast"] = float(FortFloat(next(reader)).value)
        params["cutof0"] = float(FortFloat(next(reader)).value)
        params["cutofs"] = float(FortFloat(next(reader)).value)
        params["relop"] = float(FortFloat(next(reader)).value)
        params["space"] = float(FortFloat(next(reader)).value)

    @classmethod
    def _read_molecular_params(
        cls, reader: FortranReader, params: dict[str, int | float | list[int] | None]
    ) -> None:
        """Read molecular line parameters from the reader."""
        iunitm = []
        try:
            nmlist = int(next(reader))
            if nmlist > 0:
                for _ in range(nmlist):
                    try:
                        iunitm.append(int(next(reader)))
                    except StopIteration:
                        break
            else:
                # For nmlist=0, expect a "0i" field
                try:
                    field = next(reader)
                    if not field.lower().endswith("i"):
                        raise ValueError("Expected '0i' for zero molecular lines")
                except StopIteration:
                    pass
        except StopIteration:
            pass
        params["iunitm"] = iunitm

    @classmethod
    def _read_optional_params(
        cls, reader: FortranReader, params: dict[str, int | float | list[int] | None]
    ) -> None:
        """Read optional parameters from the reader."""
        params["vtb"] = None
        params["nmu0"] = 0
        params["ang0"] = None
        params["iflux"] = 0

        try:
            params["vtb"] = float(FortFloat(next(reader)).value)
        except StopIteration:
            pass

        try:
            params["nmu0"] = int(next(reader))
            params["ang0"] = float(FortFloat(next(reader)).value)
            params["iflux"] = int(next(reader))
        except StopIteration:
            pass

    @classmethod
    def _read_params(cls, reader: FortranReader) -> dict:
        """Read parameters from a FortranReader.

        Args:
            reader: FortranReader instance to read from

        Returns:
            Dictionary of parameter values

        Raises:
            ValueError: If file format is invalid
        """
        params: dict[str, int | float | list[int] | None] = {}
        cls._read_int_params(reader, params)
        cls._read_wavelength_params(reader, params)
        cls._read_molecular_params(reader, params)
        cls._read_optional_params(reader, params)
        return params

    @classmethod
    def read(cls, directory: Path) -> Self:
        """Read configuration from fort.55 file.

        Args:
            directory: Directory containing the fort.55 file.
                      If None and path is None, raises ValueError.
            path: Complete path to the fort.55 file.
                 If provided, directory is ignored.

        Returns:
            Fort55Config object initialized from file

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid or no path is specified
        """
        path = directory / FILENAME

        with open(path) as f:
            reader = FortranReader(f.read())

        try:
            params = cls._read_params(reader)
            fort55 = cls(
                imode=OperationMode(params["imode"]),
                idstd=params["idstd"],
                iprin=params["iprin"],
                inmod=ModelType(params["inmod"]),
                intrpl=params["intrpl"],
                ichang=params["ichang"],
                ichemc=params["ichemc"],
                iophli=params["iophli"],
                nunalp=params["nunalp"],
                nunbet=params["nunbet"],
                nungam=params["nungam"],
                nunbal=params["nunbal"],
                ifreq=RadiativeTransferSolver(params["ifreq"]),
                inlte=params["inlte"],
                icontl=params["icontl"],
                inlist=params["inlist"],
                ifhe2=params["ifhe2"],
                ihydpr=params["ihydpr"],
                ihe1pr=params["ihe1pr"],
                ihe2pr=params["ihe2pr"],
                alam0=params["alam0"],
                alast=params["alast"],
                cutof0=params["cutof0"],
                cutofs=params["cutofs"],
                relop=params["relop"],
                space=params["space"],
                iunitm=params["iunitm"],
                vtb=params["vtb"],
                nmu0=params["nmu0"],
                ang0=params["ang0"],
                iflux=params["iflux"],
                directory=directory,
            )
            return fort55

        except (ValueError, IndexError, StopIteration) as e:
            raise ValueError(f"Invalid fort.55 file format: {e}")
