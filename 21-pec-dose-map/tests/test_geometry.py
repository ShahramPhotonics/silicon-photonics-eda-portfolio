from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pcell_generator import build_layout
def test_layout_nonempty():
    rects = build_layout()

    assert len(rects) >= 1
    for x0, y0, x1, y1 in rects:
        assert x1 > x0 and y1 > y0
