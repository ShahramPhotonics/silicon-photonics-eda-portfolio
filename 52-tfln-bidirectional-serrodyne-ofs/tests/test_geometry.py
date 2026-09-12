from src.model import DeviceInputs


def test_deliberately_invalid_fixture_fails():
    raised = False
    try:
        DeviceInputs(electrode_gap_m=-1.0).validate()
    except ValueError:
        raised = True
    assert raised


def test_invalid_nanometer_wavelength_is_rejected():
    raised = False
    try:
        DeviceInputs(wavelength_m=1550.0).validate()
    except ValueError:
        raised = True
    assert raised
