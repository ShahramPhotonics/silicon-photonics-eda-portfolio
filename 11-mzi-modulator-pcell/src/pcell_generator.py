#!/usr/bin/env python3
"""Parameterizable Adiabatic MZI Modulator PCell
Technology : Silicon photonic modulators
Materials  : Si 220 nm, PN junctions, Al metal lines
Parameters : Arm length, doping layers, contact pads
Stack      : klayout.db PCellDeclarationHelper
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
class MZIParams:
    arm_um: float = 400.0
    wg_um: float = 0.50
    pad_um: float = 80.0
    junction_um: float = 300.0
def build_layout(p=MZIParams()):
    w, L, jn = p.wg_um, p.arm_um, p.junction_um
    gap = 20.0
    rects = [
        (-20, -w / 2, 0, w / 2),                       # input
        (0, gap / 2, L, gap / 2 + w),                  # arm +
        (0, -gap / 2 - w, L, -gap / 2),                # arm -
        (L, -w / 2, L + 20, w / 2),                    # output
        (40, gap / 2, 40 + jn, gap / 2 + 2.0),         # PN +
        (40, -gap / 2 - 2.0, 40 + jn, -gap / 2),       # PN -
        (40 + jn / 2 - p.pad_um / 2, gap / 2 + 8, 40 + jn / 2 + p.pad_um / 2, gap / 2 + 8 + p.pad_um),
        (40 + jn / 2 - p.pad_um / 2, -gap / 2 - 8 - p.pad_um, 40 + jn / 2 + p.pad_um / 2, -gap / 2 - 8),
    ]
    return rects
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="MZI_MOD")
    print("wrote", args.out, "nrects", len(rects))
if __name__ == "__main__":
    main()
