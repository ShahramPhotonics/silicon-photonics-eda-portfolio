from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.layout import GENERIC_LAYERS, LayoutInputs, write_gds


def test_klayout_roundtrip(tmp_path=Path("/tmp/ge_pin_roundtrip")):
    try:
        import klayout.db as kdb
    except ImportError:
        return
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = write_gds(tmp_path / "device.gds", LayoutInputs())
    layout = kdb.Layout(); layout.read(str(path))
    assert layout.top_cell().name == "GE_PIN_LATERAL_CARTOON_VIROT_CLASS"
    for name in ("SI_CORE", "GE_ABSORBER", "P_CONTACT_REGION", "N_CONTACT_REGION", "CONTACT_VIA", "METAL_1"):
        assert not layout.top_cell().shapes(layout.layer(*GENERIC_LAYERS[name])).is_empty()
