#!/usr/bin/env python3
"""Run the TFLN bidirectional serrodyne analytic model."""
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
from src.model import DeviceInputs, evaluate_device, flyback_ssr_db, harmonic_powers


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TFLN bidirectional serrodyne model")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    p = DeviceInputs()
    result = evaluate_device(p)
    (args.out / "nominal.json").write_text(json.dumps(result, indent=2) + "\n")

    rows = []
    for flyback in (0.01, 0.03, 0.10):
        for eps in (0.0, 0.01, 0.02):
            q = DeviceInputs(flyback_fraction=flyback, amplitude_error_eps=eps)
            row = evaluate_device(q)
            rows.append({
                "flyback_fraction": flyback,
                "amplitude_error_eps": eps,
                "v_pi_V": row["v_pi_V"],
                "operating_conversion_efficiency": row["operating_conversion_efficiency"],
                "operating_csr_dB": row["operating_csr_dB"],
                "flyback_ssr_model_dB": flyback_ssr_db(flyback),
                "forward_modulation_depth": row["forward_modulation_depth"],
                "reverse_modulation_depth": row["reverse_modulation_depth"],
            })
    with (args.out / "sensitivity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    powers = harmonic_powers(p)
    harmonics = np.arange(-8, 9)
    values = np.array([max(powers[int(h)], 1e-18) for h in harmonics])
    plt.figure(figsize=(7.2, 4.6))
    plt.stem(harmonics, 10.0 * np.log10(values), basefmt=" ")
    plt.xlabel("Optical harmonic of the serrodyne drive")
    plt.ylabel("Relative power (dB)")
    plt.title("METHOD ESTIMATE FROM ASSUMED INPUTS — NOT MEASURED")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(args.out / "serrodyne_spectrum.png", dpi=180)
    plt.close()

    print(result["result_banner"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
