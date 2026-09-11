"""Generic multi-layer GDS layout for visualizing a lateral Ge PIN topology.

Layer numbers are project-local visualization layers, not a foundry layer map.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import klayout.db as kdb
except ImportError:  # CI still validates geometry without KLayout
    kdb = None


GENERIC_LAYERS = {
    "SI_CORE": (1, 0),
    "GE_ABSORBER": (2, 0),
    "P_CONTACT_REGION": (3, 0),
    "N_CONTACT_REGION": (4, 0),
    "CONTACT_VIA": (5, 0),
    "METAL_1": (6, 0),
    "PORT_LABEL": (10, 0),
}


@dataclass(frozen=True)
class LayoutInputs:
    ge_length_um: float = 20.0
    ge_width_um: float = 0.60
    si_input_length_um: float = 10.0
    si_width_um: float = 0.50
    contact_offset_um: float = 0.40
    contact_width_um: float = 0.60
    metal_width_um: float = 1.20

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value <= 0:
                raise ValueError(f"{name} must be > 0")
        if self.contact_offset_um < self.ge_width_um / 2:
            raise ValueError("contact_offset_um must keep p/n regions outside the intrinsic Ge width")


def rectangles(p: LayoutInputs) -> dict[str, list[tuple[float, float, float, float]]]:
    p.validate()
    x0, x1 = 0.0, p.ge_length_um
    half_ge = p.ge_width_um / 2
    cy = p.contact_offset_um + p.contact_width_um / 2
    via = 0.30
    return {
        "SI_CORE": [(-p.si_input_length_um, -p.si_width_um / 2, x1, p.si_width_um / 2)],
        "GE_ABSORBER": [(x0, -half_ge, x1, half_ge)],
        "P_CONTACT_REGION": [(x0, cy - p.contact_width_um / 2, x1, cy + p.contact_width_um / 2)],
        "N_CONTACT_REGION": [(x0, -cy - p.contact_width_um / 2, x1, -cy + p.contact_width_um / 2)],
        "CONTACT_VIA": [
            (x0 + 0.5, cy - via / 2, x1 - 0.5, cy + via / 2),
            (x0 + 0.5, -cy - via / 2, x1 - 0.5, -cy + via / 2),
        ],
        "METAL_1": [
            (x0, cy - p.metal_width_um / 2, x1 + 5, cy + p.metal_width_um / 2),
            (x0, -cy - p.metal_width_um / 2, x1 + 5, -cy + p.metal_width_um / 2),
        ],
    }


def topology_issues(p: LayoutInputs) -> list[str]:
    errors: list[str] = []
    try:
        p.validate()
    except ValueError as exc:
        return [str(exc)]
    if p.ge_width_um < 0.30:
        errors.append("generic demonstrator rule: Ge width must be >= 0.30 um")
    if p.contact_width_um < 0.40:
        errors.append("generic demonstrator rule: contact region width must be >= 0.40 um")
    if p.contact_offset_um - p.ge_width_um / 2 < 0.10:
        errors.append("generic demonstrator rule: contact-to-Ge clearance must be >= 0.10 um")
    return errors


def write_gds(path: Path, p: LayoutInputs) -> Path:
    if kdb is None:
        raise RuntimeError("KLayout Python is required to write the multi-layer GDS")
    if topology_issues(p):
        raise ValueError("layout fails cartoon topology checks: " + "; ".join(topology_issues(p)))
    layout = kdb.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("GE_PIN_LATERAL_CARTOON_VIROT_CLASS")
    scale = 1000
    for name, rects in rectangles(p).items():
        layer = layout.layer(*GENERIC_LAYERS[name])
        for x0, y0, x1, y1 in rects:
            cell.shapes(layer).insert(kdb.Box(round(x0 * scale), round(y0 * scale), round(x1 * scale), round(y1 * scale)))
    label_layer = layout.layer(*GENERIC_LAYERS["PORT_LABEL"])
    cell.shapes(label_layer).insert(kdb.Text("OPT_IN", kdb.Trans(kdb.Point(round(-p.si_input_length_um * scale), 0))))
    cell.shapes(label_layer).insert(kdb.Text("ANODE", kdb.Trans(kdb.Point(round((p.ge_length_um + 5) * scale), round((p.contact_offset_um + p.contact_width_um / 2) * scale)))))
    cell.shapes(label_layer).insert(kdb.Text("CATHODE", kdb.Trans(kdb.Point(round((p.ge_length_um + 5) * scale), round(-(p.contact_offset_um + p.contact_width_um / 2) * scale)))))
    path.parent.mkdir(parents=True, exist_ok=True)
    layout.write(str(path))
    return path
