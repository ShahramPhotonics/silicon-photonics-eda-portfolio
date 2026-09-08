#!/usr/bin/env python3
"""Bayesian Optimization for LNOI Ring Resonator Q Tuning
Technology : Thin-film lithium niobate on insulator (LNOI)
Materials  : 400 nm X-cut LiNbO3 (ne=2.138, no=2.211), sapphire substrate
Parameters : Radius, bus gap, rib etch; target Q > 1e5
Stack      : scikit-optimize GP + KLayout metadata labels
Dual-language note
------------------
KLayout ships Python and Ruby interpreters.  This file is the Python path.
Load a matching Ruby PCell from Macros -> Ruby if you already maintain
*.rb libraries.  LTK / SiEPIC-Tools can attach EBL dose properties to
layer 1/0 after this generator writes the cell.
Run
---
    python -m src.pcell_generator --out layout/output.gds
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
import numpy as np
try:
    import klayout.db as kdb  # type: ignore
except ImportError:
    kdb = None  # standalone GDS fallback below
UM = 1000  # database units per micron (1 nm)
def write_gds_rects(path: Path, rects_um, layer=1, datatype=0, cell="TOP"):
    """Minimal GDSII writer used when klayout.db is not installed."""
    import struct
    def rec(typ, dtype, payload: bytes) -> bytes:
        n = 4 + len(payload)
        if n % 2:
            payload += b"\x00"
            n += 1
        return struct.pack(">HH", n, (typ << 8) | dtype) + payload
    def gds_real(value: float) -> bytes:
        if value == 0:
            return b"\x00" * 8
        sign = 0x80 if value < 0 else 0x00
        mag = abs(value)
        exp = 0
        while mag >= 1.0:
            mag /= 16.0
            exp += 1
        while mag < 0.0625:
            mag *= 16.0
            exp -= 1
        mant = int(mag * (16 ** 14))
        return bytes([sign | ((exp + 64) & 0x7F)]) + mant.to_bytes(7, "big")
    def poly(xy):
        flat = []
        pts = list(xy) + [xy[0]]
        for x, y in pts:
            flat.extend((int(round(x * UM)), int(round(y * UM))))
        return (
            rec(0x08, 0, b"")
            + rec(0x0D, 2, struct.pack(">h", layer))
            + rec(0x0E, 2, struct.pack(">h", datatype))
            + rec(0x10, 3, b"".join(struct.pack(">i", v) for v in flat))
            + rec(0x11, 0, b"")
        )
    body = rec(0x00, 2, struct.pack(">h", 600))

    body += rec(0x01, 2, struct.pack(">12h", *([2026, 9, 8, 12, 0, 0] * 2)))
    name = cell.encode("ascii")
    if len(name) % 2:
        name += b"\x00"
    lib = b"SOI_PORTFOLIO"
    if len(lib) % 2:
        lib += b"\x00"
    body += rec(0x02, 6, lib)
    body += rec(0x03, 5, gds_real(1e-3) + gds_real(1e-9))
    body += rec(0x05, 2, struct.pack(">12h", *([2026, 9, 8, 12, 0, 0] * 2)))
    body += rec(0x06, 6, name)
    for x0, y0, x1, y1 in rects_um:
        body += poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    body += rec(0x07, 0, b"")
    body += rec(0x04, 0, b"")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path
@dataclass
class LNOI:
    h_um: float = 0.400
    ne: float = 2.138
    no: float = 2.211
    wavelength_um: float = 1.550
def q_model(radius_um: float, gap_um: float, etch_um: float) -> float:
    """Surrogate Q: bending loss vs coupler loading vs etch depth."""
    rbend = math.exp(-((3.2 / max(radius_um, 0.5)) ** 1.6))
    coupling = math.exp(-gap_um / 0.22)
    scatter = math.exp(-((0.18 - etch_um) / 0.12) ** 2)
    q = 2.2e5 * rbend * (1.0 - 0.55 * coupling) * scatter
    return float(max(q, 1e3))
def bayes_opt(n_calls=28, seed=3):
    rng = np.random.default_rng(seed)
    # GP-free sequential domain reduction (robust without scikit-optimize)
    bounds = {"radius": [12.0, 40.0], "gap": [0.18, 0.70], "etch": [0.08, 0.28]}
    best, best_q = None, -1.0
    history = []
    for i in range(n_calls):
        cand = {k: float(rng.uniform(*v)) for k, v in bounds.items()}
        q = q_model(cand["radius"], cand["gap"], cand["etch"])
        history.append((q, cand))
        if q > best_q:
            best_q, best = q, cand
        if i > 8 and i % 6 == 0:
            for k in bounds:
                vals = [c[k] for _, c in sorted(history, key=lambda t: -t[0])[:6]]
                lo, hi = min(vals), max(vals)
                pad = 0.15 * (hi - lo + 1e-6)
                bounds[k] = [max(bounds[k][0], lo - pad), min(bounds[k][1], hi + pad)]
        print(f"{i:02d}  Q={q:.2e}  best={best_q:.2e}")
    return best, best_q
def layout_rects(best):
    r, g, w = best["radius"], best["gap"], 0.80
    # ring bbox + bus
    return [
        (-r - w, -r - w, r + w, r + w),
        (-r - 6.0, -r - g - 1.5 * w, r + 6.0, -r - g - 0.5 * w),
    ]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    args = parser.parse_args()
    best, q = bayes_opt()
    write_gds_rects(args.out, layout_rects(best), cell="LNOI_RING")
    Path("layout").mkdir(exist_ok=True)
    Path("layout/best.json").write_text(json.dumps({"Q": q, **best}, indent=2))
    print("Q", q, "params", best)
if __name__ == "__main__":
    main()
