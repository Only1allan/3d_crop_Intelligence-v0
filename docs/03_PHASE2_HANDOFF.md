# 03 - How we move forward (Phase 2 handoff)

Phase 1 leaves a stable scene contract. Phase 2 adds data without touching it.

## Preconditions before Phase 2 starts

1. **In-Kit smoke test.** Run `apps/omniverse_crop_intelligence.kit` (or enable the extension in USD Composer / Isaac Sim) on a machine with Kit SDK 106+/107 and an RTX GPU. Confirm: window opens, Build creates the four `.usda` files, three markers appear on the placeholder ground, Simulate Tick recolours markers, Clear reverts. Run `tests/test_extension.py`.
2. **A real farm scan asset** at the configured path (or update `farmAssetPath`). Until the 3DGS pipeline exists, any USD terrain works.
3. **Decide the model runtime**: DSSAT-CSM SUBSTOR (Fortran, file I/O) vs a Python port (`pcse` has WOFOST; a SUBSTOR port would be new work). Recommendation: wrap DSSAT in a container behind a small HTTP service; the bridge already assumes an async external call.

## Phase 2 work packages (in order)

| # | Package | Touches | Notes |
|---|---------|---------|-------|
| 1 | AWS IoT Core transport | `phase2/ingestion.py` `start/stop/enqueue_raw` | awsiotsdk MQTT over WebSocket (SigV4). Topic `farm/<farmId>/sensor/<sensorId>/telemetry`. IoT Rules fan out to Kinesis (replay) and Timestream (history). |
| 2 | Payload adapters | new `phase2/adapters/{aws,agrifusion,farmwise}.py` | Each returns `TelemetryMessage`s in schema units (see mapping doc section 5). Unit conversions live here only. |
| 3 | Legacy back-fill | adapters + a Kit "Import legacy" button | AgriFusion: `GET /api/assessments` -> `assessment_virtual` sensors. FarmWise: `GET /api/seasons/{id}/snapshots` -> weather station + zone updates. |
| 4 | Edge aggregation | outside Kit (Greengrass / Lambda) | hourly RH/T -> `humidHours`, `humidPeriodTemperature`; daily Tmax/Tmin; SRAD from a pyranometer or Open-Meteo `shortwave_radiation_sum`. |
| 5 | SUBSTOR bridge | `phase2/substor_bridge.py run_daily` | Daily cron inside Kit (or external scheduler) -> `write_model_state` + `growthStage`. |
| 6 | SimCast bridge | `phase2/simcast_bridge.py run_daily` | Blight / fungicide units -> `cropModel:simcast*`; `status=critical` on canopy sensors; later a colour override on the scan's canopy prims. |
| 7 | History | Timestream + optional USD time samples on RUNTIME_LYR | If replay in the viewport is wanted, write `attr.Set(value, Usd.TimeCode(day))` instead of defaults. |

## Phase 3 preview

Cesium for Omniverse anchoring (`farmSensor:latitude/longitude`), the
photos -> 3DGS -> USD scan pipeline, `SIM_LYR` physics and Isaac Sim drones,
Replicator synthetic data for canopy disease detection.

## Draft "Fable Prompt Two" (Phase 2 handoff packet)

```
Role: same as Prompt One.
Context: Phase 1 is complete in /omniverse_crop_intelligence (read AGENTS.md,
docs/00_PHASE_PLAN.md, docs/01_REPOSITORY_ANALYSIS_AND_MAPPING.md first).
Objective: implement Phase 2 work packages 1-3 without changing any Phase 1
scene contract (layer order, prim paths, schema attribute names).
Constraints:
  - All live values go through phase2.runtime_writer.RuntimeWriter.
  - Transport callbacks never call USD; they enqueue TelemetryMessage.
  - Unit conversion only in adapters; the scene stores schema units.
  - Credentials from carb settings / environment; nothing hard-coded.
  - Extend tests/test_headless.py with adapter tests using recorded payloads.
Stop conditions: no SUBSTOR / SimCast maths yet (packages 5-6 are Prompt Three);
no Cesium / physics.
Outputs: adapters, transport, back-fill UI, updated docs/00_PHASE_PLAN.md.
```
