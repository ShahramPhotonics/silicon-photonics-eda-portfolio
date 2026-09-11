from src.model import DeviceInputs, absorbed_fraction, evaluate_device, responsivity_a_per_w


def test_invalid_inputs_are_rejected():
    try:
        DeviceInputs(length_um=0).validate()
    except ValueError:
        return
    raise AssertionError("zero length must be rejected")


def test_absorption_increases_with_length():
    short = absorbed_fraction(DeviceInputs(length_um=5.0))
    long = absorbed_fraction(DeviceInputs(length_um=40.0))
    assert long > short


def test_responsivity_is_positive():
    assert responsivity_a_per_w(DeviceInputs()) > 0


def test_evaluate_records_assumed_validation_level():
    result = evaluate_device()
    assert "analytically modeled" in result["validation_level"]
    assert "NOT MEASURED" in result["result_banner"]
