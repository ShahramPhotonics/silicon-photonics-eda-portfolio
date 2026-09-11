# Thin-film lithium niobate bidirectional serrodyne optical frequency shifter

> **METHOD ESTIMATE from ASSUMED inputs. Not a measurement. Not a foundry spec.**

Cycle: `F002-tfln-bidirectional-serrodyne-ofs`

This package is a transparent reduced-order analytic model instantiated from the factory generic template. Replace assumed coefficients with one internally consistent measured or calibrated source before using numbers in a design decision.

Validation level: **analytically modeled and numerically evaluated**.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py --out results
pytest -q tests
```

Outputs: `results/nominal.json`, `results/sensitivity.csv`.
