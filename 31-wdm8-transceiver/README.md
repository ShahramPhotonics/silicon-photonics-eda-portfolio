# 8-Channel WDM Transceiver Layout Generator
GitHub repository: `31-wdm8-transceiver`
## Process / materials
- Technology: Wavelength division multiplexing
- Materials: SOI PDK 220 nm Si, Ge PDs, thermal heaters
- Device parameters: 8 rings, incremental radii, bus + pads, OASIS out
- Frameworks: Hierarchical scripted PIC
## Clone and run
```bash
git clone https://github.com/ShahramPhotonics/photonics-eda-portfolio.git
cd photonics-eda-portfolio/31-wdm8-transceiver
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
