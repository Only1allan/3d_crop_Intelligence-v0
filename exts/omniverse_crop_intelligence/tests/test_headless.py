"""
Headless tests: no Omniverse Kit, only `usd-core`.

    pip install -r requirements-dev.txt
    pytest exts/omniverse_crop_intelligence/tests/test_headless.py -q

They pin the Phase 1 invariants Phase 2 will rely on:
  * sublayer order and root-layer purity
  * schema registration + typed fallbacks + allowedTokens
  * sensors defined in DATA_LYR, values in RUNTIME_LYR, nothing leaks
  * clearing RUNTIME_LYR reverts to schema fallbacks
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.dirname(HERE)
if EXT_ROOT not in sys.path:
    sys.path.insert(0, EXT_ROOT)

pxr = pytest.importorskip("pxr")
from pxr import Sdf, Usd, UsdGeom  # noqa: E402

from omniverse_crop_intelligence import settings as S  # noqa: E402
from omniverse_crop_intelligence.schema import (  # noqa: E402
    FarmSensorAPI, FarmZoneAPI, CropModelStateAPI, register_schema_plugin, is_schema_registered)
from omniverse_crop_intelligence.stage_builder import StageBuilder  # noqa: E402
from omniverse_crop_intelligence.sensor_manager import SensorManager, SensorSpec  # noqa: E402
from omniverse_crop_intelligence.phase2.runtime_writer import RuntimeWriter  # noqa: E402
from omniverse_crop_intelligence.phase2.ingestion import TelemetryIngestor, TelemetryMessage  # noqa: E402
from omniverse_crop_intelligence.phase2.substor_bridge import SubstorBridge  # noqa: E402


@pytest.fixture()
def stack(tmp_path):
    builder = StageBuilder(str(tmp_path / "layers"))
    return builder.build(overwrite=True)


def test_schema_registers_and_has_typed_fallbacks():
    assert register_schema_plugin()
    assert is_schema_registered()
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, "/S").GetPrim()
    api = FarmSensorAPI.Apply(prim)
    assert prim.GetAppliedSchemas() == ["FarmSensorAPI"]
    assert api.get("soilMoisture") == 0.0
    assert api.get("soilPH") == 7.0
    assert api.attr("soilMoisture").GetTypeName() == Sdf.ValueTypeNames.Float
    assert api.attr("latitude").GetTypeName() == Sdf.ValueTypeNames.Double
    assert set(api.attr("kind").GetMetadata("allowedTokens")) == set(S.SENSOR_KINDS)
    with pytest.raises(ValueError):
        api.set("kind", "toaster")
    assert api.attr("soilMoisture").GetMetadata("displayGroup") == "Soil"


def test_layer_stack_order_and_files(stack):
    for name in (S.ROOT_LAYER_FILE,) + S.SUBLAYER_ORDER_STRONGEST_FIRST:
        assert os.path.isfile(os.path.join(stack.output_dir, name)), name
    root = stack.stage.GetRootLayer()
    assert list(root.subLayerPaths) == [
        "./RUNTIME_LYR.usda", "./SIM_LYR.usda", "./DATA_LYR.usda", "./ASS_LYR.usda"]
    assert not root.rootPrims, "root layer must only hold subLayers"
    assert UsdGeom.GetStageUpAxis(stack.stage) == "Z"
    assert UsdGeom.GetStageMetersPerUnit(stack.stage) == 1.0
    assert stack.stage.GetDefaultPrim().GetPath() == Sdf.Path("/World")


def test_asset_layer_references_farm_scan(stack):
    scan = stack.stage.GetPrimAtPath(S.FARM_SCAN_PATH)
    assert scan
    spec = stack.asset_layer.GetPrimAtPath(S.FARM_SCAN_PATH)
    refs = spec.referenceList.prependedItems
    assert len(refs) == 1 and refs[0].assetPath == S.DEFAULT_FARM_ASSET_PATH
    # Placeholder ground keeps the viewport non-empty when the reference is unresolved.
    assert UsdGeom.Mesh(stack.stage.GetPrimAtPath(S.PLACEHOLDER_GROUND_PATH))
    assert stack.stage.GetPrimAtPath(S.SUN_LIGHT_PATH)


def test_spawn_three_test_sensors_splits_data_and_runtime(stack):
    mgr = SensorManager(stack)
    prims = mgr.spawn_test_sensors(seed_runtime_values=True)
    assert len(prims) == 3
    ids = {FarmSensorAPI(p).get("sensorId") for p in prims}
    assert ids == {"SoilProbe_NW", "WeatherStation_C", "SoilAssessment_SE"}

    # Definitions live in DATA_LYR ...
    data = stack.data_layer
    for sid in ids:
        spec = data.GetPrimAtPath(f"{S.SENSORS_PATH}/{sid}")
        assert spec and spec.specifier == Sdf.SpecifierDef
        assert "farmSensor:sensorId" in spec.properties
        assert "farmSensor:soilMoisture" not in spec.properties, "values must not be authored in DATA_LYR"
        assert data.GetPrimAtPath(f"{S.SENSORS_PATH}/{sid}/{S.SENSOR_MARKER_NAME}")
    # ... and values are overrides in RUNTIME_LYR only.
    rt = stack.runtime_layer
    probe = rt.GetPrimAtPath(f"{S.SENSORS_PATH}/SoilProbe_NW")
    assert probe and probe.specifier == Sdf.SpecifierOver
    assert probe.properties["farmSensor:soilMoisture"].default == pytest.approx(27.5)
    assert "farmSensor:sensorId" not in probe.properties

    # Composed view sees both.
    api = mgr.get_sensor("SoilProbe_NW")
    assert api.get("soilMoisture") == pytest.approx(27.5)
    assert api.get("kind") == "soil_probe"
    assert [str(t) for t in api.GetZoneRel().GetTargets()] == [f"{S.ZONES_PATH}/Zone_DemoPlot"]

    # Zone carries FarmZoneAPI + CropModelStateAPI and runtime phenology.
    zone = stack.stage.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_DemoPlot")
    assert FarmZoneAPI.IsApplied(zone) and CropModelStateAPI.IsApplied(zone)
    assert FarmZoneAPI(zone).get("growthStage") == "tuber_initiation"
    assert CropModelStateAPI(zone).get("simcastBlightRisk") == "none"  # fallback, Phase 2 fills

    # Marker colour override for status=warning landed in RUNTIME_LYR.
    marker = rt.GetPrimAtPath(f"{S.SENSORS_PATH}/WeatherStation_C/{S.SENSOR_MARKER_NAME}")
    assert marker and "primvars:displayColor" in marker.properties


def test_runtime_writer_rejects_static_attrs_and_unknown_sensor(stack):
    mgr = SensorManager(stack)
    mgr.spawn_sensor(SensorSpec("Probe_A", (1.0, 2.0, 0.0)))
    w = RuntimeWriter(stack)
    with pytest.raises(ValueError):
        w.write_sensor("Probe_A", {"sensorId": "hacked"})
    with pytest.raises(KeyError):
        w.write_sensor("Nope", {"soilMoisture": 1.0})
    w.write_sensor("Probe_A", {"soilMoisture": 12.0}, timestamp=1_700_000_000.0)
    api = mgr.get_sensor("Probe_A")
    assert api.get("soilMoisture") == 12.0
    assert api.get("lastUpdateTime") == 1_700_000_000.0


def test_clear_runtime_layer_reverts_to_definitions(stack):
    mgr = SensorManager(stack)
    mgr.spawn_test_sensors(seed_runtime_values=True)
    assert mgr.get_sensor("SoilProbe_NW").get("soilMoisture") == pytest.approx(27.5)
    StageBuilder.clear_runtime_layer(stack)
    api = mgr.get_sensor("SoilProbe_NW")
    assert api is not None, "definition must survive a runtime clear"
    assert api.get("soilMoisture") == 0.0
    assert api.get("kind") == "soil_probe"


def test_rebuild_keeps_data_layer_by_default(stack):
    mgr = SensorManager(stack)
    mgr.spawn_sensor(SensorSpec("Keep_Me", (0, 0, 0)))
    StageBuilder.save_all(stack)
    again = StageBuilder(stack.output_dir).build(overwrite=False)
    assert again.stage.GetPrimAtPath(f"{S.SENSORS_PATH}/Keep_Me")
    wiped = StageBuilder(stack.output_dir).build(overwrite=True)
    assert not wiped.stage.GetPrimAtPath(f"{S.SENSORS_PATH}/Keep_Me")


def test_ingestor_pump_writes_without_structure_changes(stack):
    mgr = SensorManager(stack)
    mgr.spawn_test_sensors(seed_runtime_values=False)
    ing = TelemetryIngestor(RuntimeWriter(stack))
    ing.enqueue(TelemetryMessage("SoilProbe_NW", {"soilMoisture": 33.3, "status": "nominal"}, 1.0))
    ing.enqueue(TelemetryMessage("WeatherStation_C", {"relativeHumidity": 91.0}, 2.0,
                                 zone_id="Zone_DemoPlot", zone_values={"ndvi": 0.7}))
    n_before = len(list(stack.stage.Traverse()))
    assert ing.pump() == 2
    assert len(list(stack.stage.Traverse())) == n_before, "runtime writes must not add prims"
    assert mgr.get_sensor("SoilProbe_NW").get("soilMoisture") == pytest.approx(33.3)
    assert FarmZoneAPI(stack.stage.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_DemoPlot")).get("ndvi") == pytest.approx(0.7)


def test_substor_bridge_aggregates_zone_sensors(stack):
    mgr = SensorManager(stack)
    mgr.spawn_test_sensors(seed_runtime_values=True)
    inp = SubstorBridge(stack.stage, RuntimeWriter(stack)).collect_daily_input("Zone_DemoPlot", "2026-09-26")
    assert inp.tmax == pytest.approx(24.1) and inp.tmin == pytest.approx(11.8)
    assert inp.soil_moisture == pytest.approx(27.5)
    assert inp.srad == 0.0, "no legacy source for SRAD; must be flagged in Phase 2"
