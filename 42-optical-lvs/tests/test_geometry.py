import math
from src.pcell_generator import build_layout

def test_layout_contains_finite_geometry():
    rects = build_layout()
    assert rects
    assert all(len(rect) == 4 for rect in rects)
    assert all(math.isfinite(value) for rect in rects for value in rect)
