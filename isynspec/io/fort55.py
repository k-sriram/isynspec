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
    """  # Wavelength and line selection parameters (required)

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
    iunitm: list[int] = field(
        default_factory=list
    )  # Unit numbers for molecular line lists

    @property
    def nmlist(self) -> int:
        """Number of additional molecular line lists."""
        return len(self.iunitm)

    # Optional parameters
    vtb: float | None = None  # Turbulent velocity [km/s]
    nmu0: int = 0  # Number of angle points for specific intensities
    ang0: float | None = None  # Minimum angle cosine
    iflux: int = 0  # Specific intensities calculation flag

    def __post_init__(self) -> None:
        """Post-initialization checks for fort.55 parameters."""
        self.validate_parameters()

    def validate_parameters(self) -> None:
        """Validate fort.55 parameters."""
        if self.alam0 > abs(self.alast):
            raise ValueError(
                f"alam0 ({self.alam0}) must be less than or equal to alast "
                f"({self.alast})"
            )
        if self.nmu0 < 0:
            raise ValueError(f"nmu0 ({self.nmu0}) cannot be negative")
        if self.vtb is None and self.nmu0 > 0:
            raise ValueError("vtb must be specified when nmu0 > 0")
        if self.ang0 is None and self.nmu0 > 0:
            raise ValueError("ang0 must be specified when nmu0 > 0")

    def write(self, path: Path) -> None:
        """Write configuration to fort.55 file.

        Args:
            path: Path where fort.55 should be written
        """
        self.validate_parameters()
        with open(path, "w") as f:
            # Basic operation parameters
            f.write(f"{self.imode.value} {self.idstd} {self.iprin}\n")

            # Model parameters
            f.write(f"{self.inmod.value} {self.intrpl} {self.ichang} {self.ichemc}\n")

            # Line physics parameters
            f.write(
                f"{self.iophli} {self.nunalp} {self.nunbet} {self.nungam} "
                f"{self.nunbal}\n"
            )
            f.write(
                f"{self.ifreq.value} {self.inlte} {self.icontl} {self.inlist} "
                f"{self.ifhe2}\n"
            )
            f.write(f"{self.ihydpr} {self.ihe1pr} {self.ihe2pr}\n")

            # Wavelength parameters
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
    def read(cls, path: Path) -> Self:  # noqa: C901 (We are imitating complex parsing)
        """Read configuration from fort.55 file.

        Args:
            path: Path to fort.55 file

        Returns:
            Fort55Config object initialized from file

        Raises:
            ValueError: If file format is invalid
        """
        with open(path) as f:
            reader = FortranReader(f.read())

        try:
            # Basic operation parameters
            imode = int(next(reader))
            idstd = int(next(reader))
            iprin = int(next(reader))

            # Model parameters
            inmod = int(next(reader))
            intrpl = int(next(reader))
            ichang = int(next(reader))
            ichemc = int(next(reader))

            # Line physics parameters
            iophli = int(next(reader))
            nunalp = int(next(reader))
            nunbet = int(next(reader))
            nungam = int(next(reader))
            nunbal = int(next(reader))

            # More line physics parameters
            ifreq = int(next(reader))
            inlte = int(next(reader))
            icontl = int(next(reader))
            inlist = int(next(reader))
            ifhe2 = int(next(reader))

            # Line profile parameters
            ihydpr = int(next(reader))
            ihe1pr = int(next(reader))
            ihe2pr = int(next(reader))

            # Wavelength parameters
            alam0 = float(FortFloat(next(reader)).value)
            alast = float(FortFloat(next(reader)).value)
            cutof0 = float(FortFloat(next(reader)).value)
            cutofs = float(FortFloat(next(reader)).value)
            relop = float(FortFloat(next(reader)).value)
            space = float(FortFloat(next(reader)).value)

            # Molecular lines
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

            # Optional parameters
            vtb = None
            nmu0 = 0
            ang0 = None
            iflux = 0

            try:
                vtb = float(FortFloat(next(reader)).value)
            except StopIteration:
                pass

            try:
                nmu0 = int(next(reader))
                ang0 = float(FortFloat(next(reader)).value)
                iflux = int(next(reader))
            except StopIteration:
                pass

            return cls(
                imode=OperationMode(imode),
                idstd=idstd,
                iprin=iprin,
                inmod=ModelType(inmod),
                intrpl=intrpl,
                ichang=ichang,
                ichemc=ichemc,
                iophli=iophli,
                nunalp=nunalp,
                nunbet=nunbet,
                nungam=nungam,
                nunbal=nunbal,
                ifreq=RadiativeTransferSolver(ifreq),
                inlte=inlte,
                icontl=icontl,
                inlist=inlist,
                ifhe2=ifhe2,
                ihydpr=ihydpr,
                ihe1pr=ihe1pr,
                ihe2pr=ihe2pr,
                alam0=alam0,
                alast=alast,
                cutof0=cutof0,
                cutofs=cutofs,
                relop=relop,
                space=space,
                iunitm=iunitm,
                vtb=vtb,
                nmu0=nmu0,
                ang0=ang0,
                iflux=iflux,
            )

        except (ValueError, IndexError, StopIteration) as e:
            raise ValueError(f"Invalid fort.55 file format: {e}")
