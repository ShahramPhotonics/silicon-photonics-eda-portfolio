#!/usr/bin/env python3
"""Genetic Algorithm Optimization of Compact Directional Couplers
Technology : SiN Photonics (300 nm silicon nitride)
Materials  : Si3N4 core n=2.000, SiO2 clad n=1.444 @ 1550 nm
Parameters : L=5-40 um, gap=200-600 nm, taper=300-900 nm, split 50:50 to 90:10
Stack      : NumPy GA + klayout.db PCell instantiation
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
BOUNDS = {'length': (5.0, 40.0), 'gap': (0.2, 0.6), 'taper': (0.3, 0.9)}  # dict of (low, high) in um unless noted
def _clip(ind):
    return {k: float(np.clip(ind[k], *BOUNDS[k])) for k in BOUNDS}
def random_individual(rng):
    return {k: float(rng.uniform(*BOUNDS[k])) for k in BOUNDS}
def crossover(a, b, rng):
    return {k: (a[k] if rng.random() < 0.5 else b[k]) for k in BOUNDS}
def mutate(ind, rng, sigma=0.08):
    out = dict(ind)
    for k, (lo, hi) in BOUNDS.items():
        if rng.random() < 0.35:
            out[k] += rng.normal(0.0, sigma * (hi - lo))
    return _clip(out)
def fitness(ind, target_split=0.5):
    """CMA split-ratio error + length penalty"""
    return geometry_score(ind, target_split)
def geometry_score(ind, target_split):
    L, gap, tw = ind["length"], ind["gap"], ind["taper"]
    # Coupled-mode stand-in: kappa ~ exp(-gap / 0.18 um)
    kappa = 0.28 * math.exp(-gap / 0.18)
    eta = math.sin(kappa * L) ** 2
    return abs(eta - target_split) + 0.01 * L + 0.05 * abs(tw - 0.45)
def layout_rects(ind):
    L, gap, w = ind["length"], ind["gap"], 0.40
    y0 = gap / 2 + w / 2
    return [
        (-L / 2, y0 - w / 2, L / 2, y0 + w / 2),
        (-L / 2, -y0 - w / 2, L / 2, -y0 + w / 2),
        (-L / 2 - ind["taper"], -0.20, -L / 2, 0.20),
        (L / 2, -0.20, L / 2 + ind["taper"], 0.20),
    ]
def evolve(pop=32, gens=24, target_split=0.5, seed=7):
    rng = np.random.default_rng(seed)
    pool = [random_individual(rng) for _ in range(pop)]
    best, best_f = None, 1e9
    for g in range(gens):
        scored = [(fitness(ind, target_split), ind) for ind in pool]
        scored.sort(key=lambda t: t[0])
        if scored[0][0] < best_f:
            best_f, best = scored[0]
        print(f"gen {g:02d}  best={best_f:.4f}  {best}")
        keep = [ind for _, ind in scored[: pop // 4]]
        kids = []
        while len(keep) + len(kids) < pop:
            a, b = rng.choice(keep, 2)
            kids.append(mutate(crossover(a, b, rng), rng))
        pool = keep + kids

    return best, best_f
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    parser.add_argument("--split", type=float, default=0.5)
    args = parser.parse_args()
    best, f = evolve(target_split=args.split)
    rects = layout_rects(best)
    write_gds_rects(args.out, rects, cell="DC_SIN")
    print("optimum", best, "fitness", f, "gds", args.out)
if __name__ == "__main__":
    main()
