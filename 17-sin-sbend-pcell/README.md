# Ultra-Low Loss S-Bend Arc Router Cell
GitHub repository: `17-sin-sbend-pcell`
## Process / materials
- Technology: SiN microwave photonics
- Materials: Si3N4 800 nm thick, high aspect ratio
- Device parameters: Bezier and cosine S-bends, zero mode-mismatch joints
- Frameworks: C1-continuous path PCell
## Clone and run
```bash
git clone https://github.com/ShahramPhotonics/photonics-eda-portfolio.git
cd photonics-eda-portfolio/17-sin-sbend-pcell
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
