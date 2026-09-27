# Omniverse Crop Intelligence

Agricultural digital twin that merges the **AgriFusion** soil platform
(`../ai-kenya`) and the **FarmWise** potato project (`../agriLegends`) into one
OpenUSD scene: codeless `FarmSensorAPI`/`FarmZoneAPI`/`CropModelStateAPI`
schemas, a tested four-layer stack (`RUNTIME > SIM > DATA > ASSET`, root layer
never authors prims), and a single enforced write path for live values.

**Hackathon demo (2026-09-27):** the demo substrate is notebook + browser —
see `docs/04_AUDIT_AND_PIVOT.md` (audit + decision record) and
`docs/05_DEMO_AND_PITCH.md` (run of show, fallbacks).

| Demo artifact | Path | Needs |
|---|---|---|
| Twin demo (tests, layer build, 30-day time-sample replay) | `notebooks/twin_demo.ipynb` | Kaggle CPU kernel (auto-fed by the scan kernel) or Colab, CPU |
| 3DGS scan pipeline PoC (train on T4, orbit render, PLY -> USD) | `notebooks/gs_scan.ipynb` | Kaggle T4x2 kernel `allankariuki/crop-gs-scan` or free Colab T4 |
| Browser splat viewer | `docs/viewer/index.html` + committed `scan.ply` / `orbit.mp4` | any static file server (`python -m http.server`) - GitHub Pages needs a public repo |
| Garden variant (vegetation scene, PSNR 27.3, 360° orbit) | `docs/viewer-garden/index.html` + committed assets | same static server |
| REAL plant growth as 4D USD (Pheno4D, 12 daily scans, session overlay) | `docs/pitch/pheno_days.png`, `assets/pheno_plant.usda` | usd-core |
| USD scan assets from the real runs | `assets/farm_scan.usda`, `assets/farm_scan_garden.usda` | usd-core |
| PLY -> USD converter | `tools/ply_to_usd_points.py` | usd-core only |
| Decision record / claims ledger | `docs/04_AUDIT_AND_PIVOT.md` | - |

**Status: Phase 1 (3D foundation) done and verified headless (21 tests on
`usd-core==26.8`); demo pipeline executed end-to-end on free Kaggle kernels
(real 3DGS training + conversion + replay); in-Kit smoke test deferred to the
post-hackathon runtime.** See `docs/00_PHASE_PLAN.md` and `docs/05`.

```
omniverse_crop_intelligence/
  AGENTS.md / CLAUDE.md          session brief for AI agents (read first)
  docs/                          plan, mapping report, architecture, Phase 2 handoff, audit
  exts/omniverse_crop_intelligence/
    config/extension.toml        Kit manifest
    omniverse_crop_intelligence/ extension.py, stage_builder.py, sensor_manager.py, scan_io.py, schema/, ui/, phase2/
    tests/                       headless (usd-core) + Kit-only (importorskip-guarded)
  apps/omniverse_crop_intelligence.kit   minimal Kit app (post-hackathon runtime)
  notebooks/                     twin_demo.ipynb, gs_scan.ipynb, replay data
  tools/                         gen_schema.py, build_layers_headless.py, ply_to_usd_points.py
  docs/viewer/                   browser splat viewer (static, no build step; Pages serves /docs)
  assets/layers/                 sample generated layer stack (usdview-able)
```

## Quick start (no Kit, no GPU needed)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt          # usd-core==26.8 pinned
pytest exts/omniverse_crop_intelligence/tests/ -q
python tools/build_layers_headless.py --out assets/layers --demo --overwrite
python tools/ply_to_usd_points.py --input scan.ply   # after gs_scan.ipynb
```

## In Omniverse Kit (post-hackathon runtime)

```bash
# Kit SDK / kit-app-template
kit apps/omniverse_crop_intelligence.kit
# or in USD Composer / Isaac Sim: Extensions > add ./exts to search paths > enable omniverse_crop_intelligence
```
Window > Crop Intelligence: Build Farm Stage, Spawn 3 Test Sensors, Simulate Telemetry Tick, Clear Runtime Layer.
