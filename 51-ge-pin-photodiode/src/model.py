"""Reduced-order electro-optic model for a lateral Si/Ge/Si PIN photodiode.

The model is an engineering calculator, not TCAD or full-wave simulation. Optical
absorption and dark current are inputs because they depend strongly on process,
strain, defects, wavelength, and the optical mode. Carrier transit response is
computed from a one-dimensional Ramo-Shockley model with uniform generation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable, Literal

import numpy as np

Q_E = 1.602176634e-19
H_PLANCK = 6.62607015e-34
C_LIGHT = 299792458.0
K_B = 1.380649e-23
EPS_0 = 8.8541878128e-12


@dataclass(frozen=True)
class DeviceInputs:
    wavelength_nm: float = 1550.0
    ge_length_um: float = 20.0
    intrinsic_width_um: float = 0.60
    ge_height_um: float = 0.50
    assumed_effective_modal_absorption_per_um: float = 0.12
    assumed_collection_efficiency: float = 0.90
    assumed_electron_velocity_m_per_s: float = 6.0e4
    assumed_hole_velocity_m_per_s: float = 6.0e4
    relative_permittivity: float = 16.0
    assumed_diode_series_resistance_ohm: float = 50.0
    instrument_load_resistance_ohm: float = 50.0
    assumed_parasitic_capacitance_f: float = 15e-15
    bias_mode: Literal["high_field_vsat", "unspecified"] = "unspecified"
    dark_current_a: float | None = None
    optical_power_w: float = 1e-3
    temperature_k: float = 300.0

    def validate(self) -> None:
        positive = {
            "wavelength_nm": self.wavelength_nm,
            "ge_length_um": self.ge_length_um,
            "intrinsic_width_um": self.intrinsic_width_um,
            "ge_height_um": self.ge_height_um,
            "assumed_electron_velocity_m_per_s": self.assumed_electron_velocity_m_per_s,
            "assumed_hole_velocity_m_per_s": self.assumed_hole_velocity_m_per_s,
            "relative_permittivity": self.relative_permittivity,
            "instrument_load_resistance_ohm": self.instrument_load_resistance_ohm,
            "temperature_k": self.temperature_k,
        }
        for name, value in positive.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")
        if self.assumed_effective_modal_absorption_per_um < 0:
            raise ValueError("assumed_effective_modal_absorption_per_um must be >= 0")
        if not 0 <= self.assumed_collection_efficiency <= 1:
            raise ValueError("assumed_collection_efficiency must be between 0 and 1")
        if self.assumed_diode_series_resistance_ohm < 0 or self.assumed_parasitic_capacitance_f < 0:
            raise ValueError("series resistance and parasitic capacitance must be >= 0")
        if self.dark_current_a is not None and self.dark_current_a < 0:
            raise ValueError("dark_current_a must be >= 0 when supplied")
        if self.bias_mode not in {"high_field_vsat", "unspecified"}:
            raise ValueError("bias_mode must be high_field_vsat or unspecified")


def absorbed_fraction(p: DeviceInputs) -> float:
    """Beer-Lambert power absorption using an effective modal coefficient."""
    p.validate()
    return -math.expm1(-p.assumed_effective_modal_absorption_per_um * p.ge_length_um)


def responsivity_a_per_w(p: DeviceInputs) -> float:
    wavelength_m = p.wavelength_nm * 1e-9
    external_qe = absorbed_fraction(p) * p.assumed_collection_efficiency
    return external_qe * Q_E * wavelength_m / (H_PLANCK * C_LIGHT)


def junction_capacitance_f(p: DeviceInputs) -> float:
    """First-order lateral parallel-plate estimate, excluding fringe fields."""
    p.validate()
    area_m2 = p.ge_height_um * 1e-6 * p.ge_length_um * 1e-6
    spacing_m = p.intrinsic_width_um * 1e-6
    return EPS_0 * p.relative_permittivity * area_m2 / spacing_m


def pair_induced_charges_c(birth_position_m: float, width_m: float) -> tuple[float, float]:
    """Ramo-Shockley induced charge from one e-h pair in a uniform weighting field.

    Position zero is the hole-collecting edge. The electron travels W-x and the
    hole travels x, so their induced charges always sum to one elementary charge.
    """
    if width_m <= 0 or not 0 <= birth_position_m <= width_m:
        raise ValueError("birth position must lie inside a positive intrinsic width")
    q_electron = Q_E * (width_m - birth_position_m) / width_m
    q_hole = Q_E * birth_position_m / width_m
    return q_electron, q_hole


def _uniform_carrier_response(
    frequencies_hz: np.ndarray, width_m: float, velocity_m_per_s: float, samples: int = 801
) -> np.ndarray:
    """Normalized current response for one carrier under uniform generation.

    Each carrier contributes q*v/W while in flight. Generation position is
    integrated numerically; this keeps the zero-frequency limit explicit and
    avoids relying on an opaque empirical transit-bandwidth constant.
    """
    x = np.linspace(0.0, width_m, samples)
    transit_s = x / velocity_m_per_s
    omega = 2 * np.pi * frequencies_hz[:, None]
    wt = omega * transit_s[None, :]
    integral = np.empty_like(wt, dtype=complex)
    integral[:] = np.where(
        np.abs(wt) < 1e-10,
        transit_s[None, :],
        (1.0 - np.exp(-1j * wt)) / np.where(omega == 0, 1.0, 1j * omega),
    )
    current_area = (velocity_m_per_s / width_m) * np.trapezoid(integral, x, axis=1) / width_m
    dc = 0.5
    current_area[frequencies_hz == 0] = dc
    return current_area / dc


def frequency_response(p: DeviceInputs, frequencies_hz: Iterable[float]) -> dict[str, np.ndarray]:
    p.validate()
    f = np.asarray(list(frequencies_hz), dtype=float)
    if f.ndim != 1 or np.any(f < 0) or not np.all(np.isfinite(f)):
        raise ValueError("frequencies_hz must be a finite non-negative 1-D sequence")
    width_m = p.intrinsic_width_um * 1e-6
    electron = _uniform_carrier_response(f, width_m, p.assumed_electron_velocity_m_per_s)
    hole = _uniform_carrier_response(f, width_m, p.assumed_hole_velocity_m_per_s)
    transit = 0.5 * (electron + hole)
    c_total = junction_capacitance_f(p) + p.assumed_parasitic_capacitance_f
    # Current-source readout loop: this is not a 50-ohm traveling-wave match.
    r_total = p.assumed_diode_series_resistance_ohm + p.instrument_load_resistance_ohm
    rc = 1.0 / (1.0 + 1j * 2 * np.pi * f * r_total * c_total)
    total = transit * rc
    return {"frequency_hz": f, "transit": transit, "rc": rc, "total": total}


def _crossing_3db(f: np.ndarray, h: np.ndarray) -> float | None:
    mag = np.abs(h)
    target = 1 / math.sqrt(2)
    below = np.flatnonzero(mag <= target)
    if not len(below):
        return None
    i = int(below[0])
    if i == 0:
        return float(f[0])
    x0, x1 = math.log10(f[i - 1]), math.log10(f[i])
    y0, y1 = mag[i - 1], mag[i]
    return 10 ** (x0 + (target - y0) * (x1 - x0) / (y1 - y0))


def evaluate_device(p: DeviceInputs, max_frequency_hz: float = 1e12) -> dict[str, object]:
    p.validate()
    frequencies = np.concatenate(([0.0], np.geomspace(1e6, max_frequency_hz, 1600)))
    response = frequency_response(p, frequencies)
    c_j = junction_capacitance_f(p)
    r = responsivity_a_per_w(p)
    photocurrent = r * p.optical_power_w
    result: dict[str, object] = {
        "inputs": asdict(p),
        "result_banner": "METHOD ESTIMATE from ASSUMED inputs. Not a measurement. Not a foundry spec. Not a reproduction of Virot 2017 or Lischke 2021.",
        "model_level": "reduced-order analytic/numerical budget; not TCAD or full-wave",
        "absorbed_fraction": absorbed_fraction(p),
        "responsivity_a_per_w": r,
        "parallel_plate_junction_capacitance_f": c_j,
        "total_capacitance_f": c_j + p.assumed_parasitic_capacitance_f,
        "photocurrent_a": photocurrent,
        "transit_3db_hz": _crossing_3db(frequencies, response["transit"]),
        "rc_3db_hz": _crossing_3db(frequencies, response["rc"]),
        "combined_3db_hz": _crossing_3db(frequencies, response["total"]),
        "bandwidth_interpretation": "high-field velocity-saturation ceiling" if p.bias_mode == "high_field_vsat" else "high-field ceiling only; operating-point bias unspecified",
        "dark_current_prediction": "not modeled; supply a measured/process-calibrated value",
    }
    if p.dark_current_a is not None:
        shot = math.sqrt(2 * Q_E * (photocurrent + p.dark_current_a))
        thermal = math.sqrt(4 * K_B * p.temperature_k / p.instrument_load_resistance_ohm)
        result["ideal_shot_noise_a_per_sqrt_hz"] = shot
        result["ideal_load_johnson_current_noise_a_per_sqrt_hz"] = thermal
        result["input_referred_noise_a_per_sqrt_hz"] = math.hypot(shot, thermal)
        result["noise_inputs"] = "measured/process-calibrated dark current plus ideal shot and Johnson noise"
    return result
