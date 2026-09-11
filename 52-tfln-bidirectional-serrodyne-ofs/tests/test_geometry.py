from src.model import DeviceInputs


def test_deliberately_invalid_fixture_fails():
    raised = False
    try:
        DeviceInputs(width_um=-1).validate()
    except ValueError:
        raised = True
    assert raised
