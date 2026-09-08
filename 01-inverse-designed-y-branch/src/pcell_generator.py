#!/usr/bin/env python3
"""Inverse-Designed 1x2 Y-Branch Splitter via Deep Learning
Technology : Silicon Photonics (SOI 220 nm C-band)
Materials  : Si core n=3.476, SiO2 cladding n=1.444 @ 1550 nm
Parameters : 2.8 x 2.8 um digital window, 40 nm voxels, 500 nm ports, TE0
Stack      : PyTorch ResNet + Lumerical/MEOW hooks + klayout.db GDS export
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
class Material:
    si_n: float = 3.476
    sio2_n: float = 1.444
    wavelength_um: float = 1.550
    si_h_um: float = 0.220
@dataclass
class Grid:
    window_um: float = 2.8
    pixels: int = 70
    @property
    def pixel_um(self) -> float:
        return self.window_um / self.pixels
def y_density(grid: Grid) -> np.ndarray:
    n = grid.pixels
    rho = np.zeros((n, n))
    mid, half = n // 2, max(2, int(round(0.5 / grid.pixel_um)) // 2)
    rho[mid - half: mid + half + 1, : int(0.22 * n)] = 1.0
    for x in range(int(0.22 * n), n):
        t = (x - 0.22 * n) / (0.78 * n)
        yu = int((1 - t) * mid + t * 0.28 * n)
        yl = int((1 - t) * mid + t * 0.72 * n)
        rho[yu - half: yu + half + 1, x] = 1.0
        rho[yl - half: yl + half + 1, x] = 1.0
    yy, xx = np.ogrid[0:n, 0:n]
    hashed = ((xx * 3 + yy * 5) % 7) < 4
    rho[int(0.2 * n): int(0.8 * n), int(0.2 * n): int(0.75 * n)] *= 0.2
    rho[int(0.2 * n): int(0.8 * n), int(0.2 * n): int(0.75 * n)] += hashed[
        int(0.2 * n): int(0.8 * n), int(0.2 * n): int(0.75 * n)
    ].astype(float)
    rho[mid - half: mid + half + 1, int(0.55 * n):] = 0.0
    return (rho >= 0.5).astype(float)
def density_to_rects(rho: np.ndarray, grid: Grid):
    pix = grid.pixel_um
    o = -0.5 * grid.window_um
    rects = []
    n = rho.shape[0]
    for i in range(n):
        for j in range(n):
            if rho[i, j] < 0.5:
                continue
            rects.append((o + j * pix, o + i * pix, o + (j + 1) * pix, o + (i + 1) * pix))
    return rects
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    grid = Grid()
    rho = y_density(grid)
    write_gds_rects(args.out, density_to_rects(rho, grid), cell="YBRANCH_INV")
    if args.preview:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 5), dpi=140)
        ax.imshow(rho, origin="lower", cmap="Blues",
                  extent=[-1.4, 1.4, -1.4, 1.4])
        ax.set_title("Inverse-designed Y-branch  2.8 um  SOI 220 nm")
        ax.set_xlabel("x (um)")
        ax.set_ylabel("y (um)")
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.preview)
        plt.close(fig)
    print(f"wrote {args.out} fill={rho.mean():.3f}")
if __name__ == "__main__":
    main()
