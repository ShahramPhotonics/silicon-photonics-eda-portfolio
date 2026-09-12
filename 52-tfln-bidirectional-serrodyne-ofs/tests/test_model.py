from dataclasses import replace
import math

from src.model import (
    DeviceInputs,
    conversion_efficiency,
    csr_db,
    evaluate_device,
    flyback_ssr_db,
    half_wave_voltage,
    modulation_depth,
)


def test_invalid_inputs_are_rejected():
    try:
        DeviceInputs(interaction_length_m=0).validate()
    except ValueError:
        return
    raise AssertionError("zero interaction length must be rejected")


def test_ideal_serrodyne_unit_efficiency():
    p = DeviceInputs(flyback_fraction=1e-4, amplitude_error_eps=0.0)
    assert conversion_efficiency(p) > 0.99
    assert evaluate_device(p)["metrics"]["ideal_conversion_efficiency"] > 0.99


def test_ssr_scales_with_flyback():
    for fraction in (0.03, 0.10):
        bound = -20.0 * math.log10(fraction)
        assert abs(flyback_ssr_db(fraction) - bound) <= 3.0
    metrics = evaluate_device()["metrics"]
    assert abs(metrics["flyback_ssr_model_F0p03_dB"] - (-20.0 * math.log10(0.03))) <= 3.0
    assert abs(metrics["flyback_ssr_model_F0p10_dB"] - (-20.0 * math.log10(0.10))) <= 3.0


def test_csr_degrades_with_amplitude_error():
    ideal = DeviceInputs(flyback_fraction=1e-4, amplitude_error_eps=0.0)
    errored = replace(ideal, amplitude_error_eps=0.02)
    degradation = csr_db(ideal) - csr_db(errored)
    assert degradation > 10.0
    assert evaluate_device(ideal)["metrics"]["amplitude_error_csr_trend"] > 10.0


def test_vpi_scales_inverse_length():
    p = DeviceInputs()
    doubled = replace(p, interaction_length_m=2.0 * p.interaction_length_m)
    ratio = half_wave_voltage(p) / half_wave_voltage(doubled)
    assert abs(ratio - 2.0) < 1e-9
    assert abs(evaluate_device(p)["metrics"]["vpi_length_scaling"] - 2.0) < 1e-9


def test_reverse_wave_walkoff_increases_with_fm_L():
    low = DeviceInputs(f_m_Hz=1.0e6, interaction_length_m=0.010)
    high = DeviceInputs(f_m_Hz=4.0e7, interaction_length_m=0.015)
    assert modulation_depth(high, reverse=True) < modulation_depth(low, reverse=True)
    assert evaluate_device()["metrics"]["reverse_walkoff_trend"] > 0


def test_wavelength_unit_consistency():
    v_short = half_wave_voltage(DeviceInputs(wavelength_m=1.50e-6))
    v_long = half_wave_voltage(DeviceInputs(wavelength_m=1.60e-6))
    assert v_long > v_short
    try:
        DeviceInputs(wavelength_m=1550.0).validate()
    except ValueError:
        return
    raise AssertionError("wavelength in nanometers must be rejected")
