# Thin-film lithium niobate bidirectional serrodyne optical frequency shifter

> **METHOD ESTIMATE from ASSUMED inputs. Not a measurement. Not a foundry spec.**

Cycle: `F002-tfln-bidirectional-serrodyne-ofs`

This package is a transparent reduced-order analytic model of a TFLN bidirectional serrodyne optical frequency shifter. It evaluates Pockels half-wave voltage, a 2π sawtooth phase ramp, flyback-limited spurious suppression, amplitude-error carrier leakage, and reverse-wave walk-off. Literature numbers from Qiu et al. and related papers are baselines, not outputs of this code.

Validation level: **analytically modeled and numerically evaluated**.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py --out results
pytest -q tests
```

Outputs: `results/nominal.json`, `results/sensitivity.csv`, `results/serrodyne_spectrum.png`.
