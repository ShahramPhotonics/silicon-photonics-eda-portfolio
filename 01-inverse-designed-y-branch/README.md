# Inverse-Designed 1x2 Y-Branch Splitter via Deep Learning
GitHub repository: `01-inverse-designed-y-branch`
## Process / materials
- Technology: Silicon Photonics (SOI 220 nm C-band)
- Materials: Si core n=3.476, SiO2 cladding n=1.444 @ 1550 nm
- Device parameters: 2.8 x 2.8 um digital window, 40 nm voxels, 500 nm ports, TE0
- Frameworks: PyTorch ResNet + Lumerical/MEOW hooks + klayout.db GDS export
## Clone and run
```bash
git clone https://github.com/ShahramPhotonics/photonics-eda-portfolio.git
cd photonics-eda-portfolio/01-inverse-designed-y-branch
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
