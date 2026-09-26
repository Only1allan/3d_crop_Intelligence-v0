"""
Central constants for the Omniverse Crop Intelligence extension.

Everything that names a layer, a prim path, a setting key, or a schema token
lives here so the other modules never hard-code strings. Pure Python: no
omni.* or pxr imports, so this file is importable in headless tests.
"""
from __future__ import annotations

EXTENSION_NAME = "omniverse_crop_intelligence"
WINDOW_TITLE = "Crop Intelligence - Farm Twin"
MENU_PATH = "Window/Crop Intelligence"

# ---------------------------------------------------------------------------
# carb.settings keys (mirrored in config/extension.toml [settings])
# ---------------------------------------------------------------------------
SETTINGS_ROOT = f"/exts/{EXTENSION_NAME}"
SETTING_FARM_ASSET_PATH = f"{SETTINGS_ROOT}/farmAssetPath"
SETTING_LAYER_OUTPUT_DIR = f"{SETTINGS_ROOT}/layerOutputDir"
SETTING_AUTO_BUILD = f"{SETTINGS_ROOT}/autoBuildOnStartup"
SETTING_SPAWN_TEST_SENSORS = f"{SETTINGS_ROOT}/spawnTestSensorsOnBuild"

DEFAULT_FARM_ASSET_PATH = "omniverse://localhost/Projects/Farm/farm_scan.usd"
DEFAULT_LAYER_OUTPUT_DIR = "${omni_documents}/omniverse_crop_intelligence/layers"

# ---------------------------------------------------------------------------
# OpenUSD layer stack.  Order matters: index 0 is the STRONGEST sublayer.
# LIVRPS: sublayers are the "L" (local opinions) and are resolved strongest-
# first, so RUNTIME overrides DATA overrides ASSET. SIM sits between RUNTIME
# and DATA so physics/collision opinions can refine semantics without ever
# being able to out-vote live telemetry.
# ---------------------------------------------------------------------------
ROOT_LAYER_FILE = "farm_twin.usda"
RUNTIME_LAYER_FILE = "RUNTIME_LYR.usda"
SIM_LAYER_FILE = "SIM_LYR.usda"
DATA_LAYER_FILE = "DATA_LYR.usda"
ASSET_LAYER_FILE = "ASS_LYR.usda"

SUBLAYER_ORDER_STRONGEST_FIRST = (
    RUNTIME_LAYER_FILE,
    SIM_LAYER_FILE,
    DATA_LAYER_FILE,
    ASSET_LAYER_FILE,
)

# ---------------------------------------------------------------------------
# Stage conventions
# ---------------------------------------------------------------------------
# Z-up / metres: matches Isaac Sim, Cesium for Omniverse and every GIS tool
# the farm data will come from. (Kit's *default* new stage is Y-up, cm.)
STAGE_UP_AXIS = "Z"
STAGE_METERS_PER_UNIT = 1.0

# Prim paths
WORLD_PATH = "/World"
FARM_PATH = "/World/Farm"
FARM_SCAN_PATH = "/World/Farm/FarmScan"
PLACEHOLDER_GROUND_PATH = "/World/Farm/PlaceholderGround"
ENVIRONMENT_PATH = "/World/Environment"
SUN_LIGHT_PATH = "/World/Environment/Sun"
ZONES_PATH = "/World/Zones"
SENSORS_PATH = "/World/Sensors"
SIMULATION_PATH = "/World/Simulation"

SENSOR_MARKER_NAME = "Marker"
SENSOR_MARKER_RADIUS_M = 0.25
PLACEHOLDER_GROUND_SIZE_M = 120.0

# ---------------------------------------------------------------------------
# Schema identifiers and attribute names (mirror schema/farmSensor/schema.usda)
# ---------------------------------------------------------------------------
FARM_SENSOR_API = "FarmSensorAPI"
FARM_ZONE_API = "FarmZoneAPI"
CROP_MODEL_STATE_API = "CropModelStateAPI"

SENSOR_KINDS = ("soil_probe", "weather_station", "canopy_probe", "satellite_virtual", "assessment_virtual")
SENSOR_SOURCES = ("synthetic", "agrifusion_assessment", "agrifusion_isda_grid",
                  "farmwise_snapshot", "farmwise_isda_baseline", "aws_iot_core")
SENSOR_STATUSES = ("unknown", "nominal", "warning", "critical", "offline")
GROWTH_STAGES = ("unplanted", "emergence", "tuber_initiation", "tuber_bulking", "maturation", "harvested")

# Marker colours (linear RGB) by kind, and status overrides written to RUNTIME.
KIND_COLORS = {
    "soil_probe": (0.55, 0.35, 0.15),
    "weather_station": (0.20, 0.55, 0.95),
    "canopy_probe": (0.20, 0.75, 0.30),
    "satellite_virtual": (0.70, 0.70, 0.70),
    "assessment_virtual": (0.85, 0.65, 0.20),
}
STATUS_COLORS = {
    "nominal": (0.20, 0.80, 0.30),
    "warning": (0.95, 0.75, 0.10),
    "critical": (0.90, 0.15, 0.15),
    "offline": (0.35, 0.35, 0.35),
}

# Telemetry attributes that Phase 2 ingestion is allowed to write. Anything
# outside this set is treated as static identity and rejected by RuntimeWriter.
SENSOR_TELEMETRY_ATTRS = (
    "farmSensor:soilMoisture", "farmSensor:soilTemperature", "farmSensor:soilPH",
    "farmSensor:soilEC", "farmSensor:soilOrganicCarbon", "farmSensor:nitrogenLevel",
    "farmSensor:phosphorusLevel", "farmSensor:potassiumLevel", "farmSensor:aluminiumLevel",
    "farmSensor:ambientTemperature", "farmSensor:temperatureMax", "farmSensor:temperatureMin",
    "farmSensor:relativeHumidity", "farmSensor:precipitation", "farmSensor:solarRadiation",
    "farmSensor:humidHours", "farmSensor:humidPeriodTemperature",
    "farmSensor:status", "farmSensor:lastUpdateTime",
)
ZONE_TELEMETRY_ATTRS = (
    "farmZone:growthStage", "farmZone:daysAfterPlanting", "farmZone:accumulatedGDD",
    "farmZone:ndvi", "farmZone:evi", "farmZone:cloudCover", "farmZone:lastUpdateTime",
)
