# Omniverse Crop Intelligence (Phase 1)

Foundation extension for an agricultural digital twin that merges the
AgriFusion soil platform and the FarmWise potato project.

What it does today:
* builds a four-sublayer OpenUSD stack (`RUNTIME > SIM > DATA > ASSET`) and opens it in the viewport
* references the 3D farm scan (`omniverse://localhost/Projects/Farm/farm_scan.usd` by default) with a placeholder ground plane fallback
* registers codeless `FarmSensorAPI`, `FarmZoneAPI` and `CropModelStateAPI` schemas
* spawns virtual sensors (Xform + marker) and writes live values only into the RUNTIME layer
* control panel: **Window > Crop Intelligence**

Not in scope yet (Phase 2): MQTT / AWS IoT Core ingestion, SUBSTOR-Potato and SimCast model execution.
See the repository `docs/` folder for the mapping report, architecture and roadmap.
