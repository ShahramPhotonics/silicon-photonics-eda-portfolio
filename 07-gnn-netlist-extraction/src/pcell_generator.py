#!/usr/bin/env python3
"""Graph Neural Network for Photonic Circuit Netlist Extraction
Technology : Electronic-photonic co-design
Materials  : Multilayer silicon / metal layout
Parameters : KLayout netlist -> NetworkX -> GNN spectral surrogate
Stack      : NetworkX + PyTorch GCN
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
class _NodeStore(dict):
    pass

class _SimpleDiGraph:
    def __init__(self):
        self.nodes = _NodeStore()
        self.edges = []
    def add_nodes_from(self, nodes):
        for node in nodes:
            self.nodes.setdefault(node, {})
    def add_edge(self, source, target, **attrs):
        self.edges.append((source, target, attrs))

def circuit_graph():
    try:
        import networkx as nx
        g = nx.DiGraph()
    except ImportError:
        g = _SimpleDiGraph()
    # 1x2 splitter -> two rings -> combiner
    nodes = ["in", "s1", "rA", "rB", "c1", "out"]
    g.add_nodes_from(nodes)
    g.add_edge("in", "s1", length_um=12.0, kind="wg")
    g.add_edge("s1", "rA", length_um=8.0, kind="wg")
    g.add_edge("s1", "rB", length_um=8.2, kind="wg")
    g.add_edge("rA", "c1", length_um=8.0, kind="wg")
    g.add_edge("rB", "c1", length_um=8.2, kind="wg")
    g.add_edge("c1", "out", length_um=10.0, kind="wg")
    g.nodes["rA"]["R_um"] = 10.0
    g.nodes["rB"]["R_um"] = 10.12
    return g
def predict_spectrum(g, wavelengths):
    """GNN stand-in: path-length interference of two ring-loaded arms."""
    n_eff = 2.44
    L_a = 2 * math.pi * g.nodes["rA"]["R_um"] + 16.0
    L_b = 2 * math.pi * g.nodes["rB"]["R_um"] + 16.4
    t = []
    for wl in wavelengths:
        dphi = 2 * math.pi * n_eff * (L_a - L_b) / wl
        t.append(float(0.5 + 0.5 * math.cos(dphi)))
    return np.array(t)
def build_layout():
    g = circuit_graph()
    wl = np.linspace(1.530, 1.570, 81)
    t = predict_spectrum(g, wl)
    Path("layout").mkdir(exist_ok=True)
    np.savetxt("layout/spectrum.csv", np.c_[wl, t], delimiter=",", header="um,T", comments="")
    return [(-6, -2, 6, 2), (-2, 4, 2, 8), (-2, -8, 2, -4)]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="GNN_NET")
    print("wrote", args.out, "nrects", len(rects))
if __name__ == "__main__":
    main()
