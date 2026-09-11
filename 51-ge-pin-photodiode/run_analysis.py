#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).parent / ".cache" / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).parent / ".cache"))
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from src.layout import GENERIC_LAYERS, LayoutInputs, topology_issues, write_gds
from src.model import DeviceInputs, evaluate_device, frequency_response


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reduced-order Ge PIN model and generic layout checks")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    p = DeviceInputs()
    result = evaluate_device(p)
    (args.out / "nominal.json").write_text(json.dumps(result, indent=2) + "\n")

    freqs = np.concatenate(([0.0], np.geomspace(1e7, 5e11, 600)))
    response = frequency_response(p, freqs)
    with (args.out / "frequency_response.csv").open("w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["frequency_hz", "transit_magnitude", "rc_magnitude", "combined_magnitude"])
        for f, ht, hr, hc in zip(freqs, response["transit"], response["rc"], response["total"]):
            writer.writerow([f, abs(ht), abs(hr), abs(hc)])

    cases = []
    for width in (0.50, 0.60, 0.70):
        for length in (15.0, 20.0, 25.0):
            q = DeviceInputs(intrinsic_width_um=width, ge_length_um=length)
            row = evaluate_device(q)
            cases.append({"sweep": "geometry", "width_um": width, "length_um": length, "alpha_eff_per_um": q.assumed_effective_modal_absorption_per_um, "parasitic_fF": q.assumed_parasitic_capacitance_f * 1e15, "series_ohm": q.assumed_diode_series_resistance_ohm, "velocity_m_per_s": q.assumed_electron_velocity_m_per_s, "absorbed_fraction": row["absorbed_fraction"], "responsivity_a_per_w": row["responsivity_a_per_w"], "rc_3db_hz": row["rc_3db_hz"], "combined_3db_hz": row["combined_3db_hz"]})
    from dataclasses import replace
    for name, values, field in (
        ("modal_absorption", (0.06, 0.12, 0.18), "assumed_effective_modal_absorption_per_um"),
        ("parasitic", (5e-15, 15e-15, 30e-15), "assumed_parasitic_capacitance_f"),
        ("series_resistance", (10.0, 50.0, 100.0), "assumed_diode_series_resistance_ohm"),
        ("carrier_velocity", (3e4, 6e4, 9e4), "assumed_electron_velocity_m_per_s"),
    ):
        for value in values:
            kwargs = {field: value}
            if field == "assumed_electron_velocity_m_per_s":
                kwargs["assumed_hole_velocity_m_per_s"] = value
            q = replace(p, **kwargs)
            row = evaluate_device(q)
            cases.append({"sweep": name, "width_um": q.intrinsic_width_um, "length_um": q.ge_length_um, "alpha_eff_per_um": q.assumed_effective_modal_absorption_per_um, "parasitic_fF": q.assumed_parasitic_capacitance_f * 1e15, "series_ohm": q.assumed_diode_series_resistance_ohm, "velocity_m_per_s": q.assumed_electron_velocity_m_per_s, "absorbed_fraction": row["absorbed_fraction"], "responsivity_a_per_w": row["responsivity_a_per_w"], "rc_3db_hz": row["rc_3db_hz"], "combined_3db_hz": row["combined_3db_hz"]})
    with (args.out / "sensitivity.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cases[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(cases)

    plt.figure(figsize=(7.2, 4.6))
    plt.semilogx(freqs[1:] / 1e9, 20 * np.log10(np.abs(response["transit"][1:])), label="Transit")
    plt.semilogx(freqs[1:] / 1e9, 20 * np.log10(np.abs(response["rc"][1:])), label="RC")
    plt.semilogx(freqs[1:] / 1e9, 20 * np.log10(np.abs(response["total"][1:])), label="Combined", linewidth=2)
    plt.axhline(-3, color="black", linestyle="--", linewidth=0.8)
    plt.xlabel("Frequency (GHz)"); plt.ylabel("Magnitude (dB)")
    plt.title("METHOD ESTIMATE FROM ASSUMED INPUTS — NOT MEASURED")
    plt.grid(True, which="both", alpha=0.25); plt.legend(); plt.tight_layout()
    plt.savefig(args.out / "frequency_response.png", dpi=180); plt.close()

    lp = LayoutInputs()
    assert not topology_issues(lp)
    write_gds(args.out / "ge_pin_generic.gds", lp)
    (args.out / "layer_map.json").write_text(json.dumps({"status": "generic visualization only; not a PDK", "layers": GENERIC_LAYERS}, indent=2) + "\n")
    print(result["result_banner"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
