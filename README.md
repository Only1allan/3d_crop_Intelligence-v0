# Omniverse Crop Intelligence

Agricultural digital twin that merges the **AgriFusion** soil platform
(`../agrifusion-aws`) and the **FarmWise** potato project (`../agriLegends`)
into one NVIDIA Omniverse Kit extension.

**Status: Phase 1 (3D foundation) implemented; in-Kit smoke test pending.**
See `docs/00_PHASE_PLAN.md`.

```
omniverse_crop_intelligence/
  AGENTS.md / CLAUDE.md          session brief for AI agents (read first)
  docs/                          plan, mapping report, architecture, Phase 2 handoff
  exts/omniverse_crop_intelligence/
    config/extension.toml        Kit manifest
    omniverse_crop_intelligence/ extension.py, stage_builder.py, sensor_manager.py, schema/, ui/, phase2/
    tests/                       test_headless.py (usd-core), test_extension.py (Kit)
  apps/omniverse_crop_intelligence.kit   minimal Kit app
  tools/                         gen_schema.py, build_layers_headless.py
  assets/layers/                 sample generated layer stack (usdview-able)
```

## Quick start (no Kit needed)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest exts/omniverse_crop_intelligence/tests/test_headless.py -q
python tools/build_layers_headless.py --out assets/layers --demo --overwrite
```

## In Omniverse Kit

```bash
# Kit SDK / kit-app-template
kit apps/omniverse_crop_intelligence.kit
# or in USD Composer / Isaac Sim: Extensions > add ./exts to search paths > enable omniverse_crop_intelligence
```
Window > Crop Intelligence: Build Farm Stage, Spawn 3 Test Sensors, Simulate Telemetry Tick, Clear Runtime Layer.
