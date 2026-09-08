# Bayesian Optimization for LNOI Ring Resonator Q Tuning
GitHub repository: `04-bo-lnoi-ring-q`
## Process / materials
- Technology: Thin-film lithium niobate on insulator (LNOI)
- Materials: 400 nm X-cut LiNbO3 (ne=2.138, no=2.211), sapphire substrate
- Device parameters: Radius, bus gap, rib etch; target Q > 1e5
- Frameworks: scikit-optimize GP + KLayout metadata labels
## Clone and run
```bash
git clone https://github.com/ShahramPhotonics/photonics-eda-portfolio.git
cd photonics-eda-portfolio/04-bo-lnoi-ring-q
python -m venv .venv && source .venv/bin/activate
pip install numpy matplotlib pytest
python -m src.pcell_generator --out layout/output.gds --preview layout/preview.png
pytest tests/test_geometry.py -q
```
Open `layout/output.gds` in KLayout.  Optional: `pip install klayout gdsfactory torch`
and re-run to use the native `klayout.db` writer.
## Dual-language KLayout + e-beam tooling
KLayout's IDE includes Ruby and Python interpreters.  This project ships a

Python generator.  After the GDS exists, install Lithography Tool Kit (LTK)
or SiEPIC-Tools from the KLayout package manager for dose assignment,
photonic PDK PCells, and EBL design-rule decks.

## Implementation status

Educational reference prototype. The generator produces deterministic layout geometry and lightweight numerical outputs; it is not a foundry-qualified design, sign-off deck, or substitute for the commercial/ML framework named in the concept specification.
