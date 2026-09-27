# AGENTS.md - Omniverse Crop Intelligence

Read this whole file at the start of every session. It is short on purpose;
the details live in `docs/`.

## What this project is

An NVIDIA Omniverse Kit extension (`exts/omniverse_crop_intelligence`) that
turns two legacy repos into one agricultural digital twin:

* `../ai-kenya` - "AgriFusion", soil assessments (pH, EC, OC, N, P, K), Next.js + Aurora + Go backend. **No IoT, no soil moisture.** (The old `../agrifusion-aws` path never existed here - see `docs/04` F2.)
* `../agriLegends` - "FarmWise", potato monitoring (daily weather, NDVI, GDD, growth stage), FastAPI + Neo4j. **No SUBSTOR, no SimCast.**

The governing spec is "Fable Prompt One" (section 8), tracked at
`docs/NVIDIA Farm Digital Twin Prompt.md`, with the user's edits:
AWS instead of Azure; extension name `omniverse_crop_intelligence`.

## Where we are

Check `docs/00_PHASE_PLAN.md` first. As of 2026-09-26: **Phase 1 done**,
awaiting an in-Kit smoke test (no Kit SDK / GPU on the dev box). Phase 2
(ingestion + model bridges) has not started.

**2026-09-27:** for the GoMyCode/NVIDIA hackathon (live pitch, deadline same
day, free Colab/Kaggle only) the demo pivoted to notebook + browser; Kit/RTX
is the post-hackathon runtime. Binding decision record:
`docs/04_AUDIT_AND_PIVOT.md` (audit, verification log, execution plan, claims
ledger). Read it before planning any demo or pitch work.

## Non-negotiable rules

1. **Phase discipline.** Do not write MQTT / AWS network code, SUBSTOR or SimCast maths, Cesium or physics until `docs/00_PHASE_PLAN.md` says that phase is active and the user asks.
2. **Layer rules.** Root layer never authors prims. Definitions -> `DATA_LYR`. Live values -> `RUNTIME_LYR` via `phase2/runtime_writer.RuntimeWriter` only. `ASS_LYR` is regenerated; never hand-edit it. Order is fixed in `settings.SUBLAYER_ORDER_STRONGEST_FIRST`.
3. **Schema changes** go in `schema/farmSensor/schema.usda`, then `python tools/gen_schema.py`, then update `settings.py` attr lists and `docs/01_*`. Never edit `generatedSchema.usda` by hand.
4. **Keep the core Kit-free.** `stage_builder.py`, `sensor_manager.py`, `schema/`, `phase2/` import only `pxr`. Only `extension.py` and `ui/` import `omni.*`.
5. **Tests must stay green**: `pytest exts/omniverse_crop_intelligence/tests/test_headless.py`. Add a test for every invariant you introduce.
6. **Kit Python is 3.10/3.11.** No 3.12+ syntax in `exts/`.
7. **Units** are schema units (see mapping doc section 5). Convert in adapters, never in scene code.

## Commands

```bash
pip install -r requirements-dev.txt
pytest exts/omniverse_crop_intelligence/tests/test_headless.py -q
python tools/build_layers_headless.py --out assets/layers --demo --overwrite
python tools/gen_schema.py
kit apps/omniverse_crop_intelligence.kit        # needs Kit SDK + GPU
```

## Docs map

* `docs/00_PHASE_PLAN.md` - phases, status table, what is open
* `docs/01_REPOSITORY_ANALYSIS_AND_MAPPING.md` - legacy variables -> schema attributes, gaps, upstream bugs
* `docs/02_ARCHITECTURE.md` - layers, prims, schemas, runtime update path, Kit glue
* `docs/03_PHASE2_HANDOFF.md` - forward plan and the draft Prompt Two
* `docs/04_AUDIT_AND_PIVOT.md` - 2026-09-27 audit, verification log, demo pivot, execution plan, pitch claims ledger
