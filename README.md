# Silicon Photonics EDA Portfolio

Fifty compact, runnable reference prototypes for silicon-photonics layout, microfabrication automation, and EDA workflows.

> **Scope:** These projects demonstrate geometry generation, data flow, and software structure. They are educational prototypes—not foundry-qualified layouts, production sign-off decks, validated device simulations, or evidence of trained ML models. Projects that name commercial tools expose integration concepts or hooks unless their README says otherwise.

## Start here

The most relevant EDA demonstrations are:

- [12 · Euler-bend ring PCell](12-euler-ring-pcell) — parametric resonator geometry.
- [21 · PEC dose map](21-pec-dose-map) — proximity-effect correction workflow concept.
- [29 · MPW floorplanner](29-mpw-floorplanner) — multi-user wafer placement.
- [41 · E-beam DRC deck](41-ebl-drc-deck) — KLayout rules plus a deliberate violation fixture.
- [47 · Optical port snapper](47-port-snapper) — connectivity and alignment checks.
- [50 · Tape-out pipeline](50-e2e-tapeout-pipeline) — end-to-end orchestration skeleton.

## Run and verify

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verify_all.py
cd 12-euler-ring-pcell && python -m src.pcell_generator --out layout/output.gds
```

Each project has its own README, generator, and geometry smoke test. Generated `layout/` outputs are intentionally ignored.

## Project index

### AI and optimization concepts

- [01 · Inverse-Designed 1x2 Y-Branch Splitter via Deep Learning](01-inverse-designed-y-branch)
- [02 · Genetic Algorithm Optimization of Compact Directional Couplers](02-ga-sin-directional-coupler)
- [03 · Physics-Informed Neural Network for Waveguide Mode Solver](03-pinn-waveguide-mode-solver)
- [04 · Bayesian Optimization for LNOI Ring Resonator Q Tuning](04-bo-lnoi-ring-q)
- [05 · Autoencoder Anomaly Detection for E-Beam Defect Masking](05-autoencoder-ebl-defects)
- [06 · Reinforcement Learning (PPO) for Automated Photonic Routing](06-ppo-photonic-router)
- [07 · Graph Neural Network for Photonic Circuit Netlist Extraction](07-gnn-netlist-extraction)
- [08 · Particle Swarm Optimization of Broadband SWG Couplers](08-pso-swg-coupler)
- [09 · Random Forest Regression for Thermal Cross-Talk in Heater Arrays](09-rf-thermal-crosstalk)
- [10 · Diffusion Model for Photonic Crystal Cavity Inverse Design](10-diffusion-phc-cavity)

### PCell development and PDK concepts

- [11 · Parameterizable Adiabatic MZI Modulator PCell](11-mzi-modulator-pcell)
- [12 · Sub-Micron Ring Resonator with Euler Bends PCell](12-euler-ring-pcell)
- [13 · Multimode Interference 2x2 Coupler PCell](13-mmi-2x2-pcell)
- [14 · Sub-Wavelength Grating Edge Coupler PCell](14-swg-edge-coupler-pcell)
- [15 · Tunable Bragg Grating Reflector PCell](15-bragg-grating-pcell)
- [16 · Electro-Optic Phase Shifter with Interdigitated PN Junctions](16-interdigitated-pn-pcell)
- [17 · Ultra-Low Loss S-Bend Arc Router Cell](17-sin-sbend-pcell)
- [18 · Optical Phased Array Emitting Antenna Element](18-opa-antenna-pcell)
- [19 · Photonic Crystal Line-Defect Waveguide (W1) PCell](19-phc-w1-pcell)
- [20 · Superconducting Single-Photon Detector Meander PCell](20-sspd-meander-pcell)

### Electron-beam lithography automation

- [21 · Proximity Effect Correction Dose Layer Map Generator](21-pec-dose-map)
- [22 · Write-Field Alignment and Stitching Marker Array](22-writefield-markers)
- [23 · Automated Layout Fracturing to Inverted Resist Masks](23-resist-tone-fracture)
- [24 · Sub-100 nm Grating Proximity Bias Calibrator](24-grating-bias-matrix)
- [25 · Grid-Snapping and DRC Clean-up for E-Beam Writers](25-ebl-grid-snap-drc)
- [26 · Automated Critical Dimension SEM Location Marking](26-cd-sem-markers)
- [27 · EBL Beam-Drift Calibration and Stitching Test Patterns](27-stitching-vernier)
- [28 · Pattern Density Uniformity Filler (Dummy Fill)](28-dummy-fill)
- [29 · Multi-User Wafer Layout Floorplanner and Multiplexer](29-mpw-floorplanner)
- [30 · OASIS vs GDSII Compression and Conversion Benchmark](30-oasis-gds-benchmark)

### Photonic systems and circuit layouts

- [31 · 8-Channel WDM Transceiver Layout Generator](31-wdm8-transceiver)
- [32 · 16x16 Optical Phased Array Transmitter Matrix](32-opa-16x16)
- [33 · Integrated Mach-Zehnder Optical Neural Network](33-onn-clements-mesh)
- [34 · Reconfigurable Ring-Resonator Optical Delay Line](34-ring-odl)
- [35 · Quantum Key Distribution Encoder Circuit](35-qkd-encoder)
- [36 · 4-Channel On-Chip CWDM Demultiplexer (Echelle Grating)](36-echelle-cwdm4)
- [37 · Integrated Photonic Gyroscope Sagnac Loop](37-sagnac-gyro)
- [38 · Optomechanical Crystal Cavity Transducer Layout](38-optomechanical-crystal)
- [39 · Monolithically Integrated Coherent Receiver Front-End](39-coherent-rx)
- [40 · MPW Test Element Group (TEG) Suite](40-mpw-teg-suite)

### DRC, LVS, and simulation APIs

- [41 · Custom KLayout DRC Script for Sub-100 nm E-Beam Rules](41-ebl-drc-deck)
- [42 · Optical Layout Versus Schematic Netlist Extractor](42-optical-lvs)
- [43 · GDSFactory-to-Lumerical FDTD Simulation Bridge](43-gdsfactory-lumerical-bridge)
- [44 · Automated Waveguide Cross-Section Lithography Simulation](44-litho-cross-section)
- [45 · Open-Source EM Solver Integration (MEOW / Tidy3D)](45-meow-tidy3d-bridge)
- [46 · Automated Electrical Rule Checker for Photonic Heaters](46-heater-erc)
- [47 · Automated Optical Connectivity Checker and Pin Snapper](47-port-snapper)
- [48 · Dynamic GDSII Multi-Layer Boolean Engine Utility](48-boolean-engine)
- [49 · OSA Data-to-Layout Mapper](49-osa-layout-mapper)
- [50 · Full End-to-End Photonic Tape-out DRC/LVS Pipeline](50-e2e-tapeout-pipeline)

## Engineering notes

- Default units are micrometres; the fallback GDSII writer uses 1 nm database units.
- Optional KLayout, gdsfactory, PyTorch, MEOW, Tidy3D, and Lumerical references are integration directions, not mandatory dependencies for the smoke tests.
- Numerical constants and design rules are illustrative. Replace them with the target PDK and fabrication process before any real design work.

## License

MIT. See [LICENSE](LICENSE).
