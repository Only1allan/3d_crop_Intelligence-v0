# Phase Plan - Omniverse Crop Intelligence

Source of truth for *where the project is*. Update the status column when a
phase item lands. Agents read this file at the start of every session (see
`AGENTS.md`).

Origin: the "Fable Prompt One" handoff packet (section 8; now tracked at
`docs/NVIDIA Farm Digital Twin Prompt.md`) with the user's edits: AWS instead
of Azure, target extension name `omniverse_crop_intelligence`, inputs
`/ai-kenya` (soil; see `docs/04` F2 - the previously documented
`/agrifusion-aws` path never existed) and `/agriLegends` (potato).

## 2026-09-27 audit and demo pivot

Full audit + external verification complete. For the hackathon window
(deadline same day, live pitch, free Colab/Kaggle only) the demo substrate is
pivoted to notebook + browser; Kit/RTX stays the post-hackathon runtime.
Binding record: `docs/04_AUDIT_AND_PIVOT.md` - read it before any demo work.

## Phase 1 - 3D foundation  (status: DONE 2026-09-26, pending in-Kit smoke test)

| # | Deliverable | Where | Status |
|---|-------------|-------|--------|
| 1 | Repository analysis and variable mapping report | `docs/01_REPOSITORY_ANALYSIS_AND_MAPPING.md` | done |
| 2 | Extension scaffold + `extension.toml` | `exts/omniverse_crop_intelligence/` | done |
| 3 | `extension.py` + omni.ui control panel + omni.usd stage build with sublayer stack | `omniverse_crop_intelligence/extension.py`, `ui/control_panel.py`, `stage_builder.py` | done |
| 4 | Codeless `FarmSensorAPI` (+ `FarmZoneAPI`, `CropModelStateAPI`) and `sensor_manager.py` with three test sensors | `schema/`, `sensor_manager.py` | done |
| 5 | Phase 2 stubs (ingestion loop, SUBSTOR bridge, SimCast bridge) documented against RUNTIME_LYR | `phase2/` | done |
| 6 | Headless test suite (usd-core) | `tests/test_headless.py` (9 tests green) | done |
| 7 | In-Kit smoke test on a machine with Kit SDK + GPU | `tests/test_extension.py`, `apps/*.kit` | **open** - no Kit on the dev box |
| 8 | Forward plan | `docs/03_PHASE2_HANDOFF.md` | done |

Stop conditions honoured: no MQTT / AWS network code, no SUBSTOR or SimCast
maths, no Isaac Sim / physics.

## Phase 2 - Data ingestion + model bridges  (status: NOT STARTED)

1. AWS IoT Core MQTT-over-WebSocket client in `phase2/ingestion.py` (`start/stop/enqueue_raw`).
2. Legacy back-fill jobs: AgriFusion `assessments` rows -> assessment_virtual sensors; FarmWise `DailySnapshot` -> weather / satellite updates.
3. Edge aggregation for SimCast (`humidHours`, `humidPeriodTemperature`) and SUBSTOR (`solarRadiation`, `temperatureMax/Min`).
4. SUBSTOR-Potato as an external daily service (DSSAT or `pcse` port); `SubstorBridge.run_daily`.
5. SimCast as an external service; `SimcastBridge.run_daily` + visual overrides.
6. Persist RUNTIME snapshots (Timestream) for history / replay.

## Phase 3 - Geospatial + simulation  (status: NOT STARTED)

1. Cesium for Omniverse anchoring using `farmSensor:latitude/longitude` and zone centroids.
2. Real 3DGS farm scan pipeline (photos -> 3DGS `.ply` -> USD) replacing the placeholder reference. *2026-09-27: a notebook-scoped PoC of this item on the Inria public capture is authorized for the hackathon demo (`docs/04` D9); production farm-scan work stays Phase 3.*
3. `SIM_LYR`: UsdPhysics collision on the scan; Isaac Sim drone / rover navigation.
4. Omniverse Replicator synthetic data for canopy disease detection.

## Phase 4 - Operations  (status: NOT STARTED)

Kit App Streaming deployment, auth, multi-farm stages, alerting back into FarmWise WhatsApp flows.
