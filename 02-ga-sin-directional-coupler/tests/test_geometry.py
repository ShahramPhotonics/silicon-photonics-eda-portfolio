from src.pcell_generator import evolve, layout_rects

def test_optimizer_produces_valid_geometry():
    best, score = evolve(pop=8, gens=3, seed=2)
    assert best is not None and score >= 0
    assert all(x1 > x0 and y1 > y0 for x0, y0, x1, y1 in layout_rects(best))
