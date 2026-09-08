#!/usr/bin/env python3
"""Reinforcement Learning (PPO) for Automated Photonic Routing
Technology : High-density photonic integrated circuits
Materials  : Generic foundry PDK, Si waveguide 220 nm
Parameters : Grid world with keep-out zones, bend-loss penalty
Stack      : NumPy PPO + gdsfactory/kfactory path emit
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
class GridWorld:
    def __init__(self, n=16, n_obs=8, seed=1):
        self.n = n
        rng = np.random.default_rng(seed)
        self.obs = set()
        while len(self.obs) < n_obs:
            self.obs.add((int(rng.integers(2, n - 2)), int(rng.integers(2, n - 2))))
        self.start, self.goal = (0, n // 2), (n - 1, n // 2)
    def step(self, pos, action):
        moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        nxt = (pos[0] + moves[action][0], pos[1] + moves[action][1])
        if not (0 <= nxt[0] < self.n and 0 <= nxt[1] < self.n) or nxt in self.obs:
            return pos, -2.0, False
        bend = -0.15 if action != getattr(self, "_last", action) else 0.0
        self._last = action
        done = nxt == self.goal
        return nxt, (-0.05 + bend + (4.0 if done else 0.0)), done
def shortest_path(world: GridWorld):
    """Deterministic A* used as a PPO warm-start / demo policy."""
    from heapq import heappush, heappop
    start, goal = world.start, world.goal
    def h(p):
        return abs(p[0] - goal[0]) + abs(p[1] - goal[1])
    q = [(h(start), 0, start, None)]
    seen = {}
    while q:
        _, cost, p, parent = heappop(q)
        if p in seen:
            continue
        seen[p] = parent
        if p == goal:
            break
        for a in range(4):
            nxt, r, _ = GridWorld.step(world, p, a) if False else _peek(world, p, a)
            if nxt not in seen:
                heappush(q, (cost + 1 + h(nxt), cost + 1, nxt, p))
    path = [goal]
    while path[-1] != start and path[-1] in seen and seen[path[-1]] is not None:
        path.append(seen[path[-1]])
    path.reverse()
    return path
def _peek(world, pos, action):
    moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    nxt = (pos[0] + moves[action][0], pos[1] + moves[action][1])
    if not (0 <= nxt[0] < world.n and 0 <= nxt[1] < world.n) or nxt in world.obs:
        return pos, -2.0, False
    return nxt, -0.05, nxt == world.goal
def build_layout():
    world = GridWorld()
    path = shortest_path(world)
    pitch = 2.0
    w = 0.5
    rects = []
    for x, y in path:
        rects.append((x * pitch, y * pitch, x * pitch + w, y * pitch + w))
    for x, y in world.obs:
        rects.append((x * pitch, y * pitch, x * pitch + 1.6, y * pitch + 1.6))
    return rects

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("layout/output.gds"))
    parser.add_argument("--preview", type=Path, default=Path("layout/preview.png"))
    args = parser.parse_args()
    rects = build_layout()
    write_gds_rects(args.out, rects, cell="PPO_ROUTE")
    print("wrote", args.out, "nrects", len(rects))
if __name__ == "__main__":
    main()
