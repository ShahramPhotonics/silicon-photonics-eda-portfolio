from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.layout import LayoutInputs, topology_issues, rectangles


def test_geometry_nonempty_and_contacts_separated():
    r = rectangles(LayoutInputs())
    assert set(r) == {"SI_CORE", "GE_ABSORBER", "P_CONTACT_REGION", "N_CONTACT_REGION", "CONTACT_VIA", "METAL_1"}
    for items in r.values():
        for x0, y0, x1, y1 in items:
            assert x1 > x0 and y1 > y0
    p = r["P_CONTACT_REGION"][0]
    n = r["N_CONTACT_REGION"][0]
    assert n[3] < p[1]


def test_nominal_generic_rules_pass():
    assert topology_issues(LayoutInputs()) == []


def test_deliberately_invalid_fixture_fails():
    errors = topology_issues(LayoutInputs(ge_width_um=0.20, contact_width_um=0.30, contact_offset_um=0.12))
    assert len(errors) >= 1
