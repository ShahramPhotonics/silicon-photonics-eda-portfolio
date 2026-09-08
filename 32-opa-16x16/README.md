# 16x16 Optical Phased Array Transmitter Matrix
GitHub repository: `32-opa-16x16`
## Process / materials
- Technology: Integrated optical LiDAR
- Materials: Si waveguides, TO phase shifters, grating emitters
- Device parameters: Binary splitter tree, N x N antennas, electrical routing
- Frameworks: Hierarchical OPA builder
## Clone and run
```bash
git clone https://github.com/ShahramPhotonics/photonics-eda-portfolio.git
cd photonics-eda-portfolio/32-opa-16x16
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
