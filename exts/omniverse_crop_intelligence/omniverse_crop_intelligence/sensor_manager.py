"""
SensorManager: spawn, list and remove virtual sensors in the farm scene.

A sensor is:
    /World/Sensors/<sensorId>          UsdGeomXform  + FarmSensorAPI   (DATA layer)
        /World/Sensors/<sensorId>/Marker  UsdGeomSphere               (DATA layer)
    /World/Sensors/<sensorId>          `over` with live values        (RUNTIME layer)

Definition (identity, kind, placement, zone link) is authored in DATA_LYR.
Measured values are NEVER authored here; they go through
phase2.runtime_writer.RuntimeWriter so they land in RUNTIME_LYR. The only
exception is `spawn_test_sensors()`, which seeds demo values through that
same writer to prove the layer split works end-to-end.

Coordinates are stage-local metres, Z-up (see settings.STAGE_UP_AXIS). The
WGS84 lat/lon attributes are carried alongside for Phase 2 geospatial
anchoring (Cesium) but do not drive placement yet.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from . import settings as S
from .schema import FarmSensorAPI, FarmZoneAPI, CropModelStateAPI
from .stage_builder import LayerStack

Vec3 = Tuple[float, float, float]
_VALID_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class SensorSpec:
    """Everything needed to define (not measure) one sensor."""
    sensor_id: str
    position: Vec3
    kind: str = "soil_probe"
    source: str = "synthetic"
    external_ref: str = ""
    zone_id: Optional[str] = None
    latitude: float = 0.0
    longitude: float = 0.0
    elevation: float = 0.0
    extra_static: Dict[str, object] = field(default_factory=dict)


@dataclass
class ZoneSpec:
    zone_id: str
    display_name: str = ""
    position: Vec3 = (0.0, 0.0, 0.0)
    source: str = "synthetic"
    external_ref: str = ""
    area_ha: float = 0.0
    variety: str = ""
    planting_date: str = ""
    centroid_latitude: float = 0.0
    centroid_longitude: float = 0.0


def _safe_name(name: str) -> str:
    if not _VALID_NAME.match(name):
        raise ValueError(f"'{name}' is not a valid USD prim name (letters, digits, underscore; no leading digit)")
    return name


class SensorManager:
    def __init__(self, stack: LayerStack):
        self._stack = stack

    @property
    def stage(self) -> Usd.Stage:
        return self._stack.stage

    # ------------------------------------------------------------------ zones
    def spawn_zone(self, spec: ZoneSpec) -> Usd.Prim:
        path = Sdf.Path(S.ZONES_PATH).AppendChild(_safe_name(spec.zone_id))
        with Usd.EditContext(self.stage, self._stack.data_layer):
            xf = UsdGeom.Xform.Define(self.stage, path)
            xf.ClearXformOpOrder()
            xf.AddTranslateOp().Set(Gf.Vec3d(*spec.position))
            prim = xf.GetPrim()
            zone = FarmZoneAPI.Apply(prim)
            zone.set_many({
                "zoneId": spec.zone_id,
                "displayName": spec.display_name or spec.zone_id,
                "source": spec.source,
                "externalRef": spec.external_ref,
                "areaHa": spec.area_ha,
                "variety": spec.variety,
                "plantingDate": spec.planting_date,
                "centroidLatitude": spec.centroid_latitude,
                "centroidLongitude": spec.centroid_longitude,
            })
            # Phase 2 model outputs get a typed home now, values later.
            CropModelStateAPI.Apply(prim)
        return prim

    # ---------------------------------------------------------------- sensors
    def spawn_sensor(self, spec: SensorSpec) -> Usd.Prim:
        """Define a sensor Xform + marker in DATA_LYR. Idempotent on sensor_id."""
        if spec.kind not in S.SENSOR_KINDS:
            raise ValueError(f"kind '{spec.kind}' not in {S.SENSOR_KINDS}")
        path = Sdf.Path(S.SENSORS_PATH).AppendChild(_safe_name(spec.sensor_id))
        with Usd.EditContext(self.stage, self._stack.data_layer):
            xf = UsdGeom.Xform.Define(self.stage, path)
            xf.ClearXformOpOrder()
            xf.AddTranslateOp().Set(Gf.Vec3d(*spec.position))
            prim = xf.GetPrim()

            api = FarmSensorAPI.Apply(prim)
            static = {
                "sensorId": spec.sensor_id,
                "kind": spec.kind,
                "source": spec.source,
                "externalRef": spec.external_ref,
                "latitude": spec.latitude,
                "longitude": spec.longitude,
                "elevation": spec.elevation,
            }
            static.update(spec.extra_static)
            api.set_many(static)
            if spec.zone_id:
                api.SetZone(Sdf.Path(S.ZONES_PATH).AppendChild(spec.zone_id))

            self._author_marker(path, spec.kind)
        return prim

    def _author_marker(self, sensor_path: Sdf.Path, kind: str) -> None:
        marker = UsdGeom.Sphere.Define(self.stage, sensor_path.AppendChild(S.SENSOR_MARKER_NAME))
        marker.CreateRadiusAttr(S.SENSOR_MARKER_RADIUS_M)
        r = S.SENSOR_MARKER_RADIUS_M
        marker.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(-r, -r, -r), Gf.Vec3f(r, r, r)]))
        marker.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*S.KIND_COLORS.get(kind, (1, 1, 1)))]))
        # Lift the marker so it sits on top of the probe position rather than half-buried.
        UsdGeom.Xformable(marker).AddTranslateOp().Set(Gf.Vec3d(0, 0, r))

    def remove_sensor(self, sensor_id: str) -> bool:
        path = Sdf.Path(S.SENSORS_PATH).AppendChild(sensor_id)
        removed = False
        for layer in (self._stack.data_layer, self._stack.runtime_layer):
            if layer.GetPrimAtPath(path):
                with Usd.EditContext(self.stage, layer):
                    self.stage.RemovePrim(path)
                removed = True
        return removed

    def list_sensors(self) -> List[Usd.Prim]:
        root = self.stage.GetPrimAtPath(S.SENSORS_PATH)
        if not root:
            return []
        return [p for p in root.GetChildren() if FarmSensorAPI.IsApplied(p)]

    def list_zones(self) -> List[Usd.Prim]:
        root = self.stage.GetPrimAtPath(S.ZONES_PATH)
        if not root:
            return []
        return [p for p in root.GetChildren() if FarmZoneAPI.IsApplied(p)]

    def get_sensor(self, sensor_id: str) -> Optional[FarmSensorAPI]:
        return FarmSensorAPI.Get(self.stage.GetPrimAtPath(Sdf.Path(S.SENSORS_PATH).AppendChild(sensor_id)))

    def sensor_summary(self) -> List[Dict[str, object]]:
        """Cheap snapshot for the UI list: id, kind, status, position, moisture, temp, RH."""
        out = []
        for prim in self.list_sensors():
            api = FarmSensorAPI(prim)
            t = UsdGeom.Xformable(prim).GetLocalTransformation().ExtractTranslation()
            out.append({
                "id": api.get("sensorId"),
                "kind": api.get("kind"),
                "status": api.get("status"),
                "position": (round(t[0], 2), round(t[1], 2), round(t[2], 2)),
                "soilMoisture": api.get("soilMoisture"),
                "ambientTemperature": api.get("ambientTemperature"),
                "relativeHumidity": api.get("relativeHumidity"),
                "lastUpdateTime": api.get("lastUpdateTime"),
            })
        return out

    # ----------------------------------------------------------- demo / tests
    #: Three sensors covering each legacy data shape plus a pure IoT probe.
    TEST_ZONE = ZoneSpec(
        zone_id="Zone_DemoPlot", display_name="Demo plot (Nyandarua, Shangi)",
        position=(0.0, 0.0, 0.0), source="farmwise_plot", external_ref="demo-plot-uuid",
        area_ha=1.0, variety="Shangi", planting_date="2026-08-15",
        centroid_latitude=-0.3031, centroid_longitude=36.3700,
    )
    TEST_SENSORS: Tuple[SensorSpec, ...] = (
        SensorSpec("SoilProbe_NW", (-20.0, 15.0, 0.0), kind="soil_probe", source="aws_iot_core",
                   external_ref="thing/soil-probe-nw", zone_id="Zone_DemoPlot",
                   latitude=-0.3029, longitude=36.3698),
        SensorSpec("WeatherStation_C", (0.0, 0.0, 0.0), kind="weather_station", source="farmwise_snapshot",
                   external_ref="snapshot-uuid", zone_id="Zone_DemoPlot",
                   latitude=-0.3031, longitude=36.3700),
        SensorSpec("SoilAssessment_SE", (25.0, -18.0, 0.0), kind="assessment_virtual", source="agrifusion_assessment",
                   external_ref="assessments.id=42", zone_id="Zone_DemoPlot",
                   latitude=-0.3033, longitude=36.3702,
                   extra_static={"soilTextureClass": "sandy_loam"}),
    )

    def spawn_test_sensors(self, seed_runtime_values: bool = True) -> List[Usd.Prim]:
        """
        Spawn the demo zone + three sensors (DATA_LYR) and, optionally, seed
        plausible readings into RUNTIME_LYR through the same writer Phase 2
        ingestion will use. Returns the sensor prims.
        """
        from .phase2.runtime_writer import RuntimeWriter  # local import: keeps phase2 optional headless

        self.spawn_zone(self.TEST_ZONE)
        prims = [self.spawn_sensor(spec) for spec in self.TEST_SENSORS]

        if seed_runtime_values:
            now = time.time()
            writer = RuntimeWriter(self._stack)
            writer.write_sensor("SoilProbe_NW", {
                "soilMoisture": 27.5, "soilTemperature": 17.9, "soilPH": 5.6,
                "nitrogenLevel": 0.14, "status": "nominal"}, timestamp=now)
            writer.write_sensor("WeatherStation_C", {
                "ambientTemperature": 19.4, "temperatureMax": 24.1, "temperatureMin": 11.8,
                "relativeHumidity": 88.0, "precipitation": 6.2, "humidHours": 9.0,
                "humidPeriodTemperature": 15.2, "status": "warning"}, timestamp=now)
            writer.write_sensor("SoilAssessment_SE", {
                "soilPH": 5.4, "soilEC": 0.15, "soilOrganicCarbon": 1.8, "nitrogenLevel": 0.14,
                "phosphorusLevel": 14.0, "potassiumLevel": 0.45, "status": "nominal"}, timestamp=now)
            writer.write_zone("Zone_DemoPlot", {
                "growthStage": "tuber_initiation", "daysAfterPlanting": 42,
                "accumulatedGDD": 410.0, "ndvi": 0.62, "evi": 0.51, "cloudCover": 8.0}, timestamp=now)
        return prims
