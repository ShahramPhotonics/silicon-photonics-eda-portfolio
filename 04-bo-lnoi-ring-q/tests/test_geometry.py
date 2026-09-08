from src.pcell_generator import bayes_opt, layout_rects

def test_optimizer_produces_valid_geometry():
    best, quality = bayes_opt(n_calls=10, seed=2)
    assert best is not None and quality > 0
    assert all(x1 > x0 and y1 > y0 for x0, y0, x1, y1 in layout_rects(best))
