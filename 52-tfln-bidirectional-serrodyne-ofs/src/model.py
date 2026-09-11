"""Reduced-order analytic model. Assumed inputs. Not a measurement."""
from __future__ import annotations

from dataclasses import dataclass
import math


Q_E = 1.602176634e-19
H_PLANCK = 6.62607015e-34
C_LIGHT = 299792458.0


@dataclass(frozen=True)
class DeviceInputs:
    wavelength_nm: float = 1550.0
    length_um: float = 20.0
    width_um: float = 0.60
    assumed_absorption_per_um: float = 0.12
    assumed_collection_efficiency: float = 0.90
    assumed_series_ohm: float = 50.0
    assumed_load_ohm: float = 50.0
    assumed_capacitance_f: float = 17.36e-15

    def validate(self) -> None:
        for name in ("wavelength_nm", "length_um", "width_um", "assumed_series_ohm",
                     "assumed_load_ohm", "assumed_capacitance_f"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")
        if self.assumed_absorption_per_um < 0:
            raise ValueError("assumed_absorption_per_um must be >= 0")
        if not 0 <= self.assumed_collection_efficiency <= 1:
            raise ValueError("assumed_collection_efficiency must be between 0 and 1")


def absorbed_fraction(p: DeviceInputs) -> float:
    p.validate()
    return -math.expm1(-p.assumed_absorption_per_um * p.length_um)


def responsivity_a_per_w(p: DeviceInputs) -> float:
    p.validate()
    qe = absorbed_fraction(p) * p.assumed_collection_efficiency
    return qe * Q_E * (p.wavelength_nm * 1e-9) / (H_PLANCK * C_LIGHT)


def rc_3db_hz(p: DeviceInputs) -> float:
    p.validate()
    tau = p.assumed_capacitance_f * (p.assumed_series_ohm + p.assumed_load_ohm)
    return 1.0 / (2.0 * math.pi * tau)


def evaluate_device(p: DeviceInputs | None = None) -> dict:
    p = p or DeviceInputs()
    p.validate()
    absorbed = absorbed_fraction(p)
    resp = responsivity_a_per_w(p)
    bandwidth = rc_3db_hz(p)
    return {
        "result_banner": "METHOD ESTIMATE FROM ASSUMED INPUTS — NOT MEASURED",
        "absorbed_fraction": absorbed,
        "responsivity_a_per_w": resp,
        "rc_3db_hz": bandwidth,
        "rc_3db_ghz": bandwidth / 1e9,
        "assumed_absorption_per_um": p.assumed_absorption_per_um,
        "length_um": p.length_um,
        "width_um": p.width_um,
        "validation_level": ["analytically modeled", "numerically evaluated"],
    }
