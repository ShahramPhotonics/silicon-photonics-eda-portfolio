#!/usr/bin/env python3
"""Particle Swarm Optimization of Broadband SWG Couplers
Technology : Sub-wavelength engineered SOI
Materials  : Si 220 nm / air cladding n=1.0
Parameters : Pitch, duty cycle, taper; sub-100 nm features
Stack      : NumPy PSO + sub-nm KLayout coordinates
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
def swg_fitness(pitch_um, duty, n_periods):
    # Subwavelength criterion + coupling heuristic
    neff = 2.1
    ok = pitch_um < 1.550 / (2 * neff)
    bw = math.exp(-((duty - 0.55) / 0.18) ** 2)
    return float((0.9 * bw if ok else 0.2) * (1.0 - abs(n_periods - 18) / 30))
def pso(n_particles=18, iters=20, seed=2):
    rng = np.random.default_rng(seed)
    pos = np.stack([
        rng.uniform(0.08, 0.28, n_particles),
        rng.uniform(0.30, 0.70, n_particles),
        rng.uniform(8, 28, n_particles),
    ], axis=1)
    vel = np.zeros_like(pos)
    pbest = pos.copy()
    pfit = np.array([swg_fitness(*row) for row in pos])
    gbest = pbest[int(pfit.argmax())].copy()
    for _ in range(iters):
        r1, r2 = rng.random(pos.shape), rng.random(pos.shape)
        vel = 0.6 * vel + 1.4 * r1 * (pbest - pos) + 1.4 * r2 * (gbest - pos)
        pos += vel
        pos[:, 0] = np.clip(pos[:, 0], 0.08, 0.28)
        pos[:, 1] = np.clip(pos[:, 1], 0.30, 0.70)
        pos[:, 2] = np.clip(pos[:, 2], 8, 28)
        fit = np.array([swg_fitness(*row) for row in pos])
        better = fit > pfit
        pbest[better] = pos[better]
        pfit[better] = fit[better]
        gbest = pbest[int(pfit.argmax())].copy()
    return gbest, float(pfit.max())
def build_layout():
    best, score = pso()
    pitch, duty, nper = float(best[0]), float(best[1]), int(round(best[2]))
    Path("layout").mkdir(exist_ok=True)
    Path("layout/best.json").write_text(json.dumps(
        {"pitch_um": pitch, "duty": duty, "n": nper, "score": score}, indent=2))
    rects = []
    x = 0.0
    w_si = duty * pitch
    for _ in range(nper):
        rects.append((x, -0.11, x + w_si, 0.11))
        x += pitch
    return rects
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="SWG_COUPLER")
    print("wrote", args.out, "nrects", len(rects))
if __name__ == "__main__":
    main()
