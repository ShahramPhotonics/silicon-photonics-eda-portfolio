"""Analytic TFLN bidirectional serrodyne optical frequency shifter.

Method estimate from assumed inputs. Not a measurement. Not foundry-qualified.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np


C_LIGHT = 299792458.0
RESULT_BANNER = "METHOD ESTIMATE FROM ASSUMED INPUTS — NOT MEASURED"


@dataclass(frozen=True)
class DeviceInputs:
    wavelength_m: float = 1.55e-6
    n_e: float = 2.14
    r33_m_per_V: float = 30.8e-12
    electrode_gap_m: float = 6.0e-6
    interaction_length_m: float = 0.010
    Gamma: float = 0.40
    f_m_Hz: float = 1.0e7
    flyback_fraction: float = 0.03
    amplitude_error_eps: float = 0.0
    n_g: float = 2.21
    n_mu: float = 2.25
    samples_per_period: int = 16384
    periods: int = 4

    def validate(self) -> None:
        for name in (
            "wavelength_m", "n_e", "r33_m_per_V", "electrode_gap_m",
            "interaction_length_m", "Gamma", "f_m_Hz", "n_g", "n_mu",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and > 0")
        if not 1e-7 <= self.wavelength_m <= 1e-4:
            raise ValueError("wavelength_m must be in meters (optical), not nanometers")
        if not 0 <= self.flyback_fraction < 1:
            raise ValueError("flyback_fraction must be in [0, 1)")
        if not math.isfinite(self.amplitude_error_eps) or abs(self.amplitude_error_eps) >= 1:
            raise ValueError("amplitude_error_eps must be finite and |eps| < 1")
        if self.samples_per_period < 256 or self.periods < 1:
            raise ValueError("FFT sampling is too coarse")


def pockels_index_shift(e_z_v_per_m: float, p: DeviceInputs | None = None) -> float:
    """delta_n_e = -0.5 * n_e^3 * r_33 * E_z."""
    p = p or DeviceInputs()
    p.validate()
    return -0.5 * p.n_e ** 3 * p.r33_m_per_V * e_z_v_per_m


def half_wave_voltage(p: DeviceInputs | None = None) -> float:
    """V_pi = lambda * G / (n_e^3 * r_33 * Gamma * L)."""
    p = p or DeviceInputs()
    p.validate()
    return p.wavelength_m * p.electrode_gap_m / (
        p.n_e ** 3 * p.r33_m_per_V * p.Gamma * p.interaction_length_m
    )


def walkoff_argument(p: DeviceInputs, reverse: bool) -> float:
    p.validate()
    mismatch = (p.n_mu + p.n_g) if reverse else (p.n_mu - p.n_g)
    return p.f_m_Hz * p.interaction_length_m * mismatch / C_LIGHT


def modulation_depth(p: DeviceInputs | None = None, reverse: bool = False) -> float:
    """Traveling-wave walk-off: sinc(f * L * (n_mu ± n_g) / c)."""
    p = p or DeviceInputs()
    return float(np.sinc(walkoff_argument(p, reverse)))


def flyback_ssr_db(flyback_fraction: float) -> float:
    """SSR_dB ≈ 20 * log10(T / t_f) = -20 * log10(F)."""
    if not math.isfinite(flyback_fraction) or flyback_fraction < 0 or flyback_fraction >= 1:
        raise ValueError("flyback_fraction must be in [0, 1)")
    if flyback_fraction == 0:
        return 120.0
    return -20.0 * math.log10(flyback_fraction)


def serrodyne_voltage(t: np.ndarray, period_s: float, v_amp: float, flyback_fraction: float) -> np.ndarray:
    tau = np.mod(t, period_s)
    if flyback_fraction <= 0:
        return -v_amp + 2.0 * v_amp * (tau / period_s)
    t_fly = flyback_fraction * period_s
    t_ramp = period_s - t_fly
    voltage = np.empty_like(tau, dtype=float)
    ramp = tau < t_ramp
    voltage[ramp] = -v_amp + 2.0 * v_amp * (tau[ramp] / t_ramp)
    voltage[~ramp] = v_amp - 2.0 * v_amp * ((tau[~ramp] - t_ramp) / t_fly)
    return voltage


def serrodyne_field(p: DeviceInputs, reverse: bool = False) -> np.ndarray:
    p.validate()
    v_pi = half_wave_voltage(p)
    v_amp = v_pi * (1.0 + p.amplitude_error_eps)
    eta = modulation_depth(p, reverse=reverse)
    period = 1.0 / p.f_m_Hz
    n = p.samples_per_period * p.periods
    t = np.arange(n, dtype=float) / (p.samples_per_period * p.f_m_Hz)
    voltage = serrodyne_voltage(t, period, v_amp, p.flyback_fraction)
    phase = math.pi * voltage / v_pi * eta
    return np.exp(1j * phase)


def harmonic_powers(p: DeviceInputs, reverse: bool = False) -> dict[int, float]:
    field = serrodyne_field(p, reverse=reverse)
    spectrum = np.fft.fft(field) / field.size
    power = np.abs(spectrum) ** 2
    total = float(power.sum())
    out = {}
    for harmonic in range(-8, 9):
        index = harmonic * p.periods
        out[harmonic] = float(power[index] / total)
    out["total"] = total
    return out


def conversion_efficiency(p: DeviceInputs, reverse: bool = False) -> float:
    return harmonic_powers(p, reverse=reverse)[1]


def csr_db(p: DeviceInputs, reverse: bool = False) -> float:
    powers = harmonic_powers(p, reverse=reverse)
    carrier = max(powers[0], 1e-18)
    return 10.0 * math.log10(powers[1] / carrier)


def evaluate_device(p: DeviceInputs | None = None) -> dict:
    p = p or DeviceInputs()
    p.validate()
    v_pi = half_wave_voltage(p)
    v_pi_double_length = half_wave_voltage(replace(p, interaction_length_m=2.0 * p.interaction_length_m))
    ideal = replace(p, flyback_fraction=1e-4, amplitude_error_eps=0.0)
    ideal_efficiency = conversion_efficiency(ideal)
    csr_ideal = csr_db(ideal)
    csr_error = csr_db(replace(ideal, amplitude_error_eps=0.02))
    reverse_low = modulation_depth(replace(p, f_m_Hz=1.0e6), reverse=True)
    reverse_high = modulation_depth(replace(p, f_m_Hz=4.0e7), reverse=True)
    forward_eta = modulation_depth(p, reverse=False)
    reverse_eta = modulation_depth(p, reverse=True)
    ssr_003 = flyback_ssr_db(0.03)
    ssr_010 = flyback_ssr_db(0.10)
    spectrum = harmonic_powers(p)
    metrics = {
        "ideal_conversion_efficiency": ideal_efficiency,
        "flyback_ssr_model": ssr_003,
        "flyback_ssr_model_F0p03_dB": ssr_003,
        "flyback_ssr_model_F0p10_dB": ssr_010,
        "amplitude_error_csr_trend": csr_ideal - csr_error,
        "vpi_length_scaling": v_pi / v_pi_double_length,
        "reverse_walkoff_trend": reverse_low - reverse_high,
    }
    return {
        "result_banner": RESULT_BANNER,
        "device": "tfln bidirectional serrodyne optical frequency shifter",
        "mechanism": "linear Pockels serrodyne phase ramp with reverse-wave walk-off",
        "v_pi_V": v_pi,
        "forward_modulation_depth": forward_eta,
        "reverse_modulation_depth": reverse_eta,
        "operating_conversion_efficiency": spectrum[1],
        "operating_csr_dB": csr_db(p),
        "operating_ssr_model_dB": flyback_ssr_db(p.flyback_fraction),
        "metrics": metrics,
        "harmonic_power_fraction": {str(k): v for k, v in spectrum.items() if k != "total"},
        "validation_level": ["analytically modeled", "numerically evaluated"],
        "limitations": [
            "Assumed inputs. Not measured.",
            "No FDTD mode solver and no HFSS extraction.",
        ],
    }
