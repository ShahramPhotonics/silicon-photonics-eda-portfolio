#!/usr/bin/env python3
"""Custom KLayout DRC Script for Sub-100 nm E-Beam Rules
Technology : EBL microfabrication verification
Materials  : Silicon photonic nanofabrication constraints
Parameters : Min width 50 nm, gap 60 nm, acute angles, enclosure
Stack      : KLayout .drc Python/Ruby deck
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
DRC_TEXT = """
# src/drc_rules.drc  -- sub-100 nm e-beam
source($input || "layout/output.gds")
report("ebl_drc", "layout/drc_report.lyrdb")
si = input(1, 0)
si.width(0.050, euclidian).output("min_width_50nm")
si.space(0.060, euclidian).output("min_space_60nm")
si.dangle(0, 45).output("acute_angle")
"""
def check_rects(rects):
    errors = []
    for x0, y0, x1, y1 in rects:
        if min(x1 - x0, y1 - y0) < 0.050:
            errors.append(("width", (x0, y0, x1, y1)))
    return errors
def build_layout():
    return [(0, 0, 2.0, 0.50), (3.0, 0, 3.04, 2.0)]  # second is a DRC fail demo
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="DRC_DEMO")
    Path("src").mkdir(exist_ok=True)
    Path("src/drc_rules.drc").write_text(DRC_TEXT)
    errs = check_rects(rects)
    Path("layout").mkdir(exist_ok=True)
    Path("layout/drc_python.json").write_text(json.dumps(errs, indent=2))
    print("errors", errs)
if __name__ == "__main__":
    main()
