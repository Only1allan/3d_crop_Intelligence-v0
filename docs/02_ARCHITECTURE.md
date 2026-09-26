# 02 - Architecture (Phase 1)

## Layer stack (LIVRPS "L")

```
farm_twin.usda                 root: subLayers + stage metadata only, never prims
 |- RUNTIME_LYR.usda   strong  live telemetry overrides, model outputs, status colours
 |- SIM_LYR.usda               physics / collision / robots (Phase 3), empty scope now
 |- DATA_LYR.usda              zones + sensor definitions (identity, placement, links)
 '- ASS_LYR.usda       weak    3D farm scan reference, placeholder ground, sun light
```

Rules (enforced by `StageBuilder.validate` and the headless tests):
1. The root layer authors no prims.
2. Values are never authored in DATA_LYR; definitions are never authored in RUNTIME_LYR (`RuntimeWriter` rejects static attributes).
3. ASS_LYR is regenerated on every build; DATA/RUNTIME survive unless `overwrite=True`.
4. Sublayer paths are relative (`./X.usda`) so the folder can be copied to Nucleus as a unit.

## Prim hierarchy

```
/World                              (defaultPrim, Z-up, 1 m)
  /World/Farm
    /World/Farm/FarmScan            Xform, references @omniverse://localhost/Projects/Farm/farm_scan.usd@
    /World/Farm/PlaceholderGround   Mesh 120x120 m, shown until the scan resolves
  /World/Environment/Sun            DistantLight
  /World/Zones                      Scope
    /World/Zones/<zoneId>           Xform + FarmZoneAPI + CropModelStateAPI
  /World/Sensors                    Scope
    /World/Sensors/<sensorId>       Xform + FarmSensorAPI, rel farmSensor:zone -> zone
      .../Marker                    Sphere r=0.25 m, colour by kind (DATA) or status (RUNTIME override)
  /World/Simulation                 Scope (SIM_LYR, empty)
```

## Schemas

Codeless API schemas (`schema/farmSensor/schema.usda` -> `generatedSchema.usda`
+ `plugInfo.json`, registered at runtime with `Plug.Registry().RegisterPlugins`).
No compiled code, so the same files work in Kit's USD and in `usd-core`.

* `FarmSensorAPI` - identity, provenance, WGS84 position, soil chemistry, atmosphere; `displayGroup` metadata groups them in Kit's Property panel.
* `FarmZoneAPI` - plot / season identity, management, phenology, canopy indices.
* `CropModelStateAPI` - SUBSTOR and SimCast outputs (Phase 2 writes).

Python wrappers in `schema/farm_sensor_api.py` add `Apply/Get/IsApplied`, token validation against `allowedTokens`, and `set_many` inside one `Sdf.ChangeBlock`.

## Runtime update path (why there is no stage reload)

`RuntimeWriter` wraps every write in `Usd.EditContext(stage, RUNTIME_LYR)`.
Only attribute *values* change; prim structure never does. USD emits a
fine-grained `ObjectsChanged` notice, Kit's Fabric/Hydra updates the changed
attributes, and the viewport redraws without recomposition. Clearing the
runtime layer is one `layer.Clear()`.

Threading: USD writes happen on the main thread only. Transport callbacks
(Phase 2 MQTT) enqueue; `TelemetryIngestor.pump()` drains on Kit's update loop.

## Kit integration

* `extension.py` registers the schema, builds the stack on disk, then `omni.usd.get_context().open_stage(root)` so Stage / Property / Viewport share the stage. Sdf layers are singletons per identifier, so edit contexts on the on-disk sublayers hit the same composition.
* Dependencies (extension.toml): `omni.kit.uiapp`, `omni.ui`, `omni.usd`, `omni.client`, `omni.kit.commands`, `omni.kit.viewport.window`, `omni.kit.viewport.utility`, `omni.kit.menu.utils`.
* Settings: `farmAssetPath`, `layerOutputDir`, `autoBuildOnStartup`, `spawnTestSensorsOnBuild`.

## Test strategy

* `tests/test_headless.py` (pytest + usd-core) - layer invariants, schema, data/runtime split, ingestor pump, bridge aggregation. Runs anywhere.
* `tests/test_extension.py` (omni.kit.test) - window exists, build opens stage in omni.usd, tick + clear. Needs Kit SDK.
* `tools/build_layers_headless.py --demo` - produces `assets/layers/` for inspection in usdview / USD Composer.
