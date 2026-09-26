"""
RuntimeWriter: the ONLY sanctioned path for live values into the stage.

Why it exists
-------------
OpenUSD composes the strongest opinion per attribute across the sublayer
stack. By always writing through `Usd.EditContext(stage, RUNTIME_LYR)` we get:

* Overrides, not edits: DATA_LYR keeps the sensor definition, RUNTIME_LYR
  gets an `over "SoilProbe_NW" { float farmSensor:soilMoisture = 27.5 }`.
* No stage reloads: attribute value changes emit a fine-grained
  Usd.Notice.ObjectsChanged; Kit's Fabric/Hydra picks up only the changed
  attributes. Nothing recomposes because we never change prim *structure*.
* Cheap reset: StageBuilder.clear_runtime_layer() wipes live state.

Phase 2 ingestion (AWS IoT Core / MQTT) and the model bridges call this and
nothing else. They must never hold a Usd.Attribute across frames or write
outside an EditContext.
"""
from __future__ import annotations

import time
from typing import Dict, Optional

from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .. import settings as S
from ..schema import FarmSensorAPI, FarmZoneAPI, CropModelStateAPI
from ..stage_builder import LayerStack


class RuntimeWriter:
    def __init__(self, stack: LayerStack):
        self._stack = stack

    @property
    def stage(self) -> Usd.Stage:
        return self._stack.stage

    # ---------------------------------------------------------------- sensors
    def write_sensor(self, sensor_id: str, values: Dict[str, object],
                     timestamp: Optional[float] = None, save: bool = False) -> None:
        """
        Override telemetry attributes on /World/Sensors/<sensor_id> in RUNTIME_LYR.

        `values` keys may be short ("soilMoisture") or qualified
        ("farmSensor:soilMoisture"). Keys outside settings.SENSOR_TELEMETRY_ATTRS
        raise: identity/placement is DATA-layer business.
        """
        prim = self.stage.GetPrimAtPath(Sdf.Path(S.SENSORS_PATH).AppendChild(sensor_id))
        api = FarmSensorAPI.Get(prim)
        if api is None:
            raise KeyError(f"No FarmSensorAPI sensor named '{sensor_id}'")
        qualified = {api._qualify(k): v for k, v in values.items()}
        bad = [k for k in qualified if k not in S.SENSOR_TELEMETRY_ATTRS]
        if bad:
            raise ValueError(f"Not writable at runtime (static definition attrs): {bad}")
        qualified.setdefault("farmSensor:lastUpdateTime", float(timestamp if timestamp is not None else time.time()))

        with Usd.EditContext(self.stage, self._stack.runtime_layer):
            api.set_many(qualified)
            status = qualified.get("farmSensor:status")
            if status in S.STATUS_COLORS:
                self._override_marker_color(prim, S.STATUS_COLORS[status])
        if save:
            self._stack.runtime_layer.Save()

    def _override_marker_color(self, sensor_prim: Usd.Prim, rgb) -> None:
        marker = UsdGeom.Sphere(sensor_prim.GetChild(S.SENSOR_MARKER_NAME))
        if marker:
            marker.GetDisplayColorAttr().Set(Vt.Vec3fArray([Gf.Vec3f(*rgb)]))

    # ------------------------------------------------------------------ zones
    def write_zone(self, zone_id: str, values: Dict[str, object],
                   timestamp: Optional[float] = None, save: bool = False) -> None:
        prim = self.stage.GetPrimAtPath(Sdf.Path(S.ZONES_PATH).AppendChild(zone_id))
        api = FarmZoneAPI.Get(prim)
        if api is None:
            raise KeyError(f"No FarmZoneAPI zone named '{zone_id}'")
        qualified = {api._qualify(k): v for k, v in values.items()}
        bad = [k for k in qualified if k not in S.ZONE_TELEMETRY_ATTRS]
        if bad:
            raise ValueError(f"Not writable at runtime: {bad}")
        qualified.setdefault("farmZone:lastUpdateTime", float(timestamp if timestamp is not None else time.time()))
        with Usd.EditContext(self.stage, self._stack.runtime_layer):
            api.set_many(qualified)
        if save:
            self._stack.runtime_layer.Save()

    def write_model_state(self, zone_id: str, values: Dict[str, object], save: bool = False) -> None:
        """Phase 2 model bridges write SUBSTOR / SimCast outputs here."""
        prim = self.stage.GetPrimAtPath(Sdf.Path(S.ZONES_PATH).AppendChild(zone_id))
        api = CropModelStateAPI.Get(prim)
        if api is None:
            raise KeyError(f"No CropModelStateAPI on zone '{zone_id}'")
        with Usd.EditContext(self.stage, self._stack.runtime_layer):
            api.set_many({api._qualify(k): v for k, v in values.items()})
        if save:
            self._stack.runtime_layer.Save()
