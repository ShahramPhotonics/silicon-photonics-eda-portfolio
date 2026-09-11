# Lateral Si/Ge/Si PIN photodiode engineering model

> **METHOD ESTIMATE from ASSUMED inputs. Not a measurement. Not a foundry spec. Not a reproduction of Virot 2017 or Lischke 2021.**

This project couples a parameterized, generic multi-layer layout with a transparent reduced-order electro-optic model. It addresses a gap in project 39: that project sketches a coherent receiver floorplan but does not model a photodiode.

Validation level: **analytically modeled and numerically evaluated**. This is not TCAD, full-wave optical simulation, measured silicon, a PDK cell, or a foundry-qualified layout. The GDS layer numbers are project-local visualization layers.

The model calculates Beer-Lambert modal absorption from an **assumed effective modal** coefficient; responsivity from absorbed fraction and assumed collection efficiency; a parallel-plate estimate of lateral junction capacitance; separate electron and hole transit responses by numerical integration of a one-dimensional Ramo-Shockley model; RC and combined frequency response; and optional ideal shot/Johnson noise when a measured or process-calibrated dark current is supplied. It intentionally does not predict dark current.

Defaults are method-demonstration assumptions, not claims about a fabricated device. Replace them with values from one internally consistent measured device or calibrated solver before using the result in a design decision. Responsivity is linear in collection efficiency and in `1-exp(-alpha_eff*L)`; the example's 45.8 GHz is unrelated to Virot's reported greater-than-50 GHz measurement. In particular, do not combine the dimensions and bandwidth of the Lischke fin device with the responsivity or dark current of the Virot architecture.

Optical length `L` runs along the waveguide; carrier transit width `Wi` runs across it:

```text
                   optical propagation, L  --->
 p-Si/contact  ===================================
                    Ge absorber cartoon
               <---- carrier transit, Wi ---->
 n-Si/contact  ===================================
```

The transit model assumes a uniform weighting field and uniform lateral pair-generation position. For a pair born at `x`, the induced charges are `q_e=q(Wi-x)/Wi` and `q_h=qx/Wi`, so their sum is exactly `q`. The velocity inputs are high-field assumptions. With `bias_mode=unspecified`, every transit bandwidth is labeled a high-field ceiling rather than an operating-point prediction.

The RC transfer is the current-source readout loop `I_load/I_photo = 1/[1+j*omega*C_total*(R_series+R_load)]`. `R_series` is an assumed diode slab/contact resistance and `R_load` is the instrument load; this is not RF matching. The assumed 15 fF parasitic exceeds the 2.36 fF parallel-plate junction estimate in the example. Fringing fields, mixed Si/Ge dielectric, depletion-voltage dependence, pads and package interconnect are omitted.

## What this GDS is not

The cell `GE_PIN_LATERAL_CARTOON_VIROT_CLASS` is a top-view cartoon of the lateral Virot architecture class: an optical guide, a rectangular Ge region, separate Si-side p/n regions, vias, metals and labels. It does not encode Virot's process, a Ge seed/recess, implant dose, silicide enclosure, GSG pads, heterojunction band offsets, or any foundry layer map. It is not the biconcave Lischke fin. The checks are connectivity and visualization predicates, not a PDK DRC deck.

Run from this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py --out results
pytest -q tests
```

Outputs include `nominal.json`, frequency and sensitivity CSV files, a frequency-response plot, a generic GDS, and an explicit layer-map receipt. The GDS writer requires KLayout's Python package; the compact model only needs NumPy and Matplotlib.

The automated checks name and verify: absorption monotonicity and zero/long-length limits; the quantum responsivity bound; frequency-response DC normalization and roll-off; Ramo-Shockley pair charge conservation at midpoint and edge birth; the expected equal-velocity transit-bandwidth ratio; slower-carrier tail behavior; capacitance scaling; series-resistance effect; refusal to invent dark current; zero optical/dark-current shot noise; invalid inputs; separate metal topology; a deliberately invalid named topology fixture; and KLayout GDS round trip when KLayout is installed.

Primary literature used to define the research target:

- L. Virot et al., “Integrated waveguide PIN photodiodes exploiting lateral Si/Ge/Si heterojunction,” *Optics Express* 25, 19487–19496 (2017), https://doi.org/10.1364/OE.25.019487.
- S. Lischke et al., “Ultra-fast germanium photodiode with 3-dB bandwidth of 265 GHz,” *Nature Photonics* 15, 925–931 (2021), https://doi.org/10.1038/s41566-021-00893-w.
- S. Shekhar et al., “Roadmapping the next generation of silicon photonics,” *Nature Communications* 15, 751 (2024), https://doi.org/10.1038/s41467-024-44750-0.

The Virot device is a lateral Si/Ge/Si heterojunction with contacts on silicon and tens-of-micrometre absorber lengths. Lischke's later device is a different biconcave Ge-fin process with complementary in-situ-doped silicon. The citations define prior art and demand; none of their measured values is used as a package preset. All defaults remain labeled assumptions.
