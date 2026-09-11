from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.model import Q_E, DeviceInputs, absorbed_fraction, evaluate_device, frequency_response, pair_induced_charges_c, responsivity_a_per_w


def test_absorption_boundaries_and_monotonicity():
    assert absorbed_fraction(DeviceInputs(ge_length_um=1e-9)) < 1e-8
    lengths = (5.0, 10.0, 20.0, 40.0)
    values = [absorbed_fraction(DeviceInputs(ge_length_um=x)) for x in lengths]
    assert all(a < b for a, b in zip(values, values[1:]))
    assert values[-1] < 1.0


def test_responsivity_obeys_quantum_limit():
    p = DeviceInputs()
    ideal = 1.602176634e-19 * p.wavelength_nm * 1e-9 / (6.62607015e-34 * 299792458.0)
    assert 0 < responsivity_a_per_w(p) < ideal


def test_zero_absorption_and_long_device_limits():
    assert absorbed_fraction(DeviceInputs(assumed_effective_modal_absorption_per_um=0.0)) == 0
    assert responsivity_a_per_w(DeviceInputs(assumed_effective_modal_absorption_per_um=0.0)) == 0
    long = DeviceInputs(ge_length_um=1e6)
    assert abs(absorbed_fraction(long) - 1.0) < 1e-12


def test_frequency_response_dc_and_rolloff():
    f = np.array([0.0, 1e9, 1e10, 1e11, 1e12])
    h = frequency_response(DeviceInputs(), f)
    assert abs(h["total"][0] - 1) < 1e-12
    assert abs(h["total"][-1]) < abs(h["total"][1])


def test_width_tradeoff_is_physical():
    narrow = evaluate_device(DeviceInputs(intrinsic_width_um=0.45))
    wide = evaluate_device(DeviceInputs(intrinsic_width_um=0.75))
    assert narrow["parallel_plate_junction_capacitance_f"] > wide["parallel_plate_junction_capacitance_f"]
    assert narrow["transit_3db_hz"] > wide["transit_3db_hz"]


def test_dark_current_is_not_fabricated():
    result = evaluate_device(DeviceInputs())
    assert "not modeled" in result["dark_current_prediction"]
    assert "input_referred_noise_a_per_sqrt_hz" not in result


def test_invalid_inputs_are_rejected():
    try:
        evaluate_device(DeviceInputs(intrinsic_width_um=0.0))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid width was accepted")


def test_ramo_shockley_pair_charge_conservation_and_edges():
    width = 0.6e-6
    qe, qh = pair_induced_charges_c(width / 2, width)
    assert abs(qe - Q_E / 2) < 1e-30
    assert abs(qh - Q_E / 2) < 1e-30
    assert abs(qe + qh - Q_E) < 1e-30
    qe, qh = pair_induced_charges_c(0.0, width)
    assert qe == Q_E and qh == 0.0


def test_transit_bandwidth_ratio_and_slower_carrier_tail():
    p = DeviceInputs(bias_mode="high_field_vsat")
    nominal = evaluate_device(p)
    tau = p.intrinsic_width_um * 1e-6 / p.assumed_electron_velocity_m_per_s
    ratio = nominal["transit_3db_hz"] * tau
    assert 0.44 < ratio < 0.56
    slow_holes = evaluate_device(DeviceInputs(assumed_hole_velocity_m_per_s=3e4, bias_mode="high_field_vsat"))
    assert slow_holes["transit_3db_hz"] < nominal["transit_3db_hz"]


def test_capacitance_scaling_and_rc_resistance_effect():
    base = evaluate_device(DeviceInputs())
    double_l = evaluate_device(DeviceInputs(ge_length_um=40.0))
    assert abs(double_l["parallel_plate_junction_capacitance_f"] / base["parallel_plate_junction_capacitance_f"] - 2) < 1e-12
    low_r = evaluate_device(DeviceInputs(assumed_diode_series_resistance_ohm=10.0))
    assert low_r["rc_3db_hz"] > base["rc_3db_hz"]


def test_noise_requires_supplied_dark_current_and_zero_shot_limit():
    zero = evaluate_device(DeviceInputs(optical_power_w=0.0, dark_current_a=0.0))
    assert zero["ideal_shot_noise_a_per_sqrt_hz"] == 0
    assert zero["input_referred_noise_a_per_sqrt_hz"] > 0  # Johnson term remains
