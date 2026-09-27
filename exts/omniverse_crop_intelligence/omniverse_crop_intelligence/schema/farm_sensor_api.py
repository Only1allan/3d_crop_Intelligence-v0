"""
Python wrappers around the codeless API schemas.

Codeless schemas give us typed attributes but not the generated
`FarmSensorAPI.Get()/Apply()/CreateSoilMoistureAttr()` classes that
usdGenSchema would emit for a compiled schema. These small wrappers restore
that ergonomics for the handful of call sites that need it (StageBuilder,
SensorManager, Phase 2 bridges) and give one place to validate tokens.

They deliberately do NOT cache attribute handles: every call goes back to the
prim so edits made through Usd.EditContext land in the intended layer.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pxr import Sdf, Usd

from .. import settings as S


class _AppliedAPI:
    """Base for single-apply API wrappers."""

    SCHEMA_NAME: str = ""
    NAMESPACE: str = ""

    def __init__(self, prim: Usd.Prim):
        if not prim or not prim.IsValid():
            raise ValueError(f"{self.SCHEMA_NAME}: invalid prim")
        self._prim = prim

    # -- schema lifecycle ---------------------------------------------------
    @classmethod
    def Apply(cls, prim: Usd.Prim) -> "_AppliedAPI":
        """Apply the API schema (no-op if already applied) and return a wrapper."""
        if cls.SCHEMA_NAME not in prim.GetAppliedSchemas():
            if not prim.ApplyAPI(cls.SCHEMA_NAME):
                raise RuntimeError(
                    f"Could not apply {cls.SCHEMA_NAME} to {prim.GetPath()}; is the schema plugin registered?"
                )
        return cls(prim)

    @classmethod
    def Get(cls, prim: Usd.Prim) -> Optional["_AppliedAPI"]:
        """Return a wrapper if the schema is applied, else None."""
        if prim and prim.IsValid() and cls.SCHEMA_NAME in prim.GetAppliedSchemas():
            return cls(prim)
        return None

    @classmethod
    def IsApplied(cls, prim: Usd.Prim) -> bool:
        return bool(prim) and cls.SCHEMA_NAME in prim.GetAppliedSchemas()

    @property
    def prim(self) -> Usd.Prim:
        return self._prim

    # -- generic attribute access -------------------------------------------
    def qualify(self, name: str) -> str:
        """Short attr name -> namespaced ("soilMoisture" -> "farmSensor:soilMoisture")."""
        return name if ":" in name else f"{self.NAMESPACE}:{name}"

    # Backwards-compatible alias for older call sites.
    _qualify = qualify

    def attr(self, name: str) -> Usd.Attribute:
        a = self._prim.GetAttribute(self._qualify(name))
        if not a:
            raise KeyError(f"{self.SCHEMA_NAME} has no attribute {self._qualify(name)}")
        return a

    def get(self, name: str, time=Usd.TimeCode.Default()) -> Any:
        return self.attr(name).Get(time)

    def set(self, name: str, value: Any, time=Usd.TimeCode.Default()) -> None:
        a = self.attr(name)
        allowed = a.GetMetadata("allowedTokens")
        if allowed and value not in list(allowed):
            raise ValueError(f"{a.GetPath()}: '{value}' not in allowedTokens {list(allowed)}")
        a.Set(value, time)

    def set_many(self, values: Dict[str, Any], time=Usd.TimeCode.Default()) -> None:
        """Batch set inside one Sdf.ChangeBlock so listeners get a single notice."""
        with Sdf.ChangeBlock():
            for k, v in values.items():
                self.set(k, v, time)


class FarmSensorAPI(_AppliedAPI):
    SCHEMA_NAME = S.FARM_SENSOR_API
    NAMESPACE = "farmSensor"

    # convenience accessors for the attributes the prompt calls out by name
    def GetSensorIdAttr(self): return self.attr("sensorId")
    def GetKindAttr(self): return self.attr("kind")
    def GetStatusAttr(self): return self.attr("status")
    def GetSoilMoistureAttr(self): return self.attr("soilMoisture")
    def GetAmbientTemperatureAttr(self): return self.attr("ambientTemperature")
    def GetRelativeHumidityAttr(self): return self.attr("relativeHumidity")
    def GetNitrogenLevelAttr(self): return self.attr("nitrogenLevel")
    def GetLastUpdateTimeAttr(self): return self.attr("lastUpdateTime")

    def GetZoneRel(self) -> Usd.Relationship:
        return self._prim.GetRelationship("farmSensor:zone")

    def SetZone(self, zone_path: str) -> None:
        rel = self.GetZoneRel() or self._prim.CreateRelationship("farmSensor:zone")
        rel.SetTargets([Sdf.Path(zone_path)])


class FarmZoneAPI(_AppliedAPI):
    SCHEMA_NAME = S.FARM_ZONE_API
    NAMESPACE = "farmZone"


class CropModelStateAPI(_AppliedAPI):
    SCHEMA_NAME = S.CROP_MODEL_STATE_API
    NAMESPACE = "cropModel"
