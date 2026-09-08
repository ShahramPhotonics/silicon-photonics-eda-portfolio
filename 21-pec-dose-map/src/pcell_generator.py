#!/usr/bin/env python3
"""Proximity Effect Correction Dose Layer Map Generator
Technology : Sub-100 nm EBL lithography
Materials  : HSQ resist on silicon
Parameters : Density map, dense vs isolated dose layers
Stack      : Polygon density + layer split
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
def density_map(binary: np.ndarray, blur=3) -> np.ndarray:
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(binary, blur, mode="edge")
    # mean filter
    out = np.zeros_like(binary, dtype=float)
    k = 2 * blur + 1
    for i in range(binary.shape[0]):
        for j in range(binary.shape[1]):
            out[i, j] = pad[i:i + k, j:j + k].mean()
    return out
def build_layout():
    n = 24
    binary = np.zeros((n, n))
    binary[8:16, 4:20] = 1  # dense bar
    binary[2, 2] = 1        # isolated pixel
    dens = density_map(binary)
    rects = []
    pix = 0.08
    for i in range(n):
        for j in range(n):
            if binary[i, j] < 0.5:
                continue
            # isolated features get a larger drawn bias proxy
            b = 0.0 if dens[i, j] > 0.4 else 0.02
            rects.append((j * pix - b, i * pix - b, (j + 1) * pix + b, (i + 1) * pix + b))
    Path("layout").mkdir(exist_ok=True)
    np.save("layout/density.npy", dens)
    return rects
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="PEC_MAP")
    print("wrote", args.out, "nrects", len(rects))
if __name__ == "__main__":
    main()
