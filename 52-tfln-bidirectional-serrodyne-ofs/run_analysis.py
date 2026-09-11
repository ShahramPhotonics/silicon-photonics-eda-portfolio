#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from src.model import DeviceInputs, evaluate_device


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generic analytic model")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    nominal = evaluate_device()
    (args.out / "nominal.json").write_text(json.dumps(nominal, indent=2) + "\n")
    rows = []
    for length in (10.0, 20.0, 30.0):
        for absorption in (0.06, 0.12, 0.18):
            row = evaluate_device(DeviceInputs(length_um=length, assumed_absorption_per_um=absorption))
            rows.append({
                "length_um": length,
                "absorption_per_um": absorption,
                "absorbed_fraction": row["absorbed_fraction"],
                "responsivity_a_per_w": row["responsivity_a_per_w"],
                "rc_3db_ghz": row["rc_3db_ghz"],
            })
    with (args.out / "sensitivity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(nominal["result_banner"])
    print(json.dumps(nominal, indent=2))


if __name__ == "__main__":
    main()
