"""
PHASE 2 STUB - SUBSTOR-Potato bridge.

Scope guard: the SUBSTOR equations (thermal time, tuber initiation, dry matter
partitioning, RUE-driven assimilation, water/N stress factors) are NOT
implemented here and will not be implemented inside the Omniverse codebase.
SUBSTOR runs as an external daily service; this bridge only moves data.

Neither legacy project contains SUBSTOR. FarmWise (`agriLegends`) advances
growth stage by calendar days and asks an LLM for yield, so Phase 2 will
introduce the model itself (DSSAT SUBSTOR-Potato or a Python port such as
`pcse`), fed from the stage:

    inputs per zone (daily)        from FarmSensorAPI on sensors linked by farmSensor:zone
      SRAD  solarRadiation         MJ/m2/day   (new IoT / satellite-derived)
      TMAX  temperatureMax         degC
      TMIN  temperatureMin         degC
      RAIN  precipitation          mm
      SW    soilMoisture           % VWC -> converted to mm per soil layer
      N     nitrogenLevel          % -> kg/ha using bulk density (Phase 2 parameter)
    inputs per zone (static)       from FarmZoneAPI
      plantingDate, variety (cultivar coefficients table lives with the model)
    outputs per zone               written to CropModelStateAPI via RuntimeWriter
      substorTotalDryMatter, substorTuberDryMatter, substorLeafAreaIndex,
      substorTuberFreshYield, substorLastRunTime; and farmZone:growthStage

Contract with the scene: reads happen on the main thread, the model call is
awaited off-thread, and outputs are written back through RuntimeWriter so
they compose as RUNTIME_LYR overrides (no reload, undo-able, clearable).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from pxr import Usd

from .. import settings as S
from ..schema import FarmSensorAPI, FarmZoneAPI
from .runtime_writer import RuntimeWriter


@dataclass
class SubstorDailyInput:
    zone_id: str
    date: str               # YYYY-MM-DD
    srad: float             # MJ/m2/day
    tmax: float             # degC
    tmin: float             # degC
    rain: float             # mm
    soil_moisture: float    # % VWC (zone mean)
    nitrogen: float         # % total N (zone mean)


class SubstorBridge:
    def __init__(self, stage: Usd.Stage, writer: RuntimeWriter):
        self._stage = stage
        self._writer = writer

    def collect_daily_input(self, zone_id: str, date: str) -> SubstorDailyInput:
        """
        Aggregate the sensors linked to a zone into one SUBSTOR daily record.
        Implemented now (pure reads) so Phase 2 only has to add the model call.
        Missing drivers come back as 0.0 and must be flagged by the caller.
        """
        zone_path = f"{S.ZONES_PATH}/{zone_id}"
        sensors: List[FarmSensorAPI] = []
        for prim in self._stage.GetPrimAtPath(S.SENSORS_PATH).GetChildren():
            api = FarmSensorAPI.Get(prim)
            if api and zone_path in [str(t) for t in api.GetZoneRel().GetTargets()]:
                sensors.append(api)

        def mean(name: str) -> float:
            vals = [api.get(name) for api in sensors if api.get(name) not in (None, 0.0)]
            return float(sum(vals) / len(vals)) if vals else 0.0

        return SubstorDailyInput(
            zone_id=zone_id, date=date,
            srad=mean("solarRadiation"), tmax=mean("temperatureMax"), tmin=mean("temperatureMin"),
            rain=mean("precipitation"), soil_moisture=mean("soilMoisture"), nitrogen=mean("nitrogenLevel"),
        )

    async def run_daily(self, zone_id: str, date: str) -> None:
        """
        TODO(Phase 2):
          1. inp = self.collect_daily_input(zone_id, date)          (main thread)
          2. out = await external_substor_service.step(inp)          (off-thread / HTTP)
          3. self._writer.write_model_state(zone_id, {...outputs...}) (main thread)
          4. self._writer.write_zone(zone_id, {"growthStage": out.stage})
        """
        raise NotImplementedError("Phase 2: SUBSTOR runs as an external service")
