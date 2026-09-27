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
from typing import Dict, List, Optional

from pxr import Usd

from .. import settings as S
from ..schema import FarmSensorAPI, FarmZoneAPI
from .runtime_writer import RuntimeWriter


@dataclass
class SubstorDailyInput:
    zone_id: str
    date: str               # YYYY-MM-DD
    srad: Optional[float]             # MJ/m2/day
    tmax: Optional[float]             # degC
    tmin: Optional[float]             # degC
    rain: Optional[float]             # mm
    soil_moisture: Optional[float]    # % VWC (zone mean)
    nitrogen: Optional[float]         # % total N (zone mean)
    # None means NO sensor authored a measurement for that driver on the
    # zone; 0.0 means a real measurement of zero. Phase 2 must treat these
    # differently (substitute satellite-derived SRAD vs. a dry day).


class SubstorBridge:
    def __init__(self, stage: Usd.Stage, writer: RuntimeWriter):
        self._stage = stage
        self._writer = writer

    def collect_daily_input(self, zone_id: str, date: str) -> SubstorDailyInput:
        """
        Aggregate the sensors linked to a zone into one SUBSTOR daily record.
        Implemented now (pure reads) so Phase 2 only has to add the model call.

        A driver is None when no zone-linked sensor has an AUTHORED value for
        it: schema fallbacks (e.g. soilMoisture == 0.0 on a probe that never
        measured) are defaults, not measurements. Authored zeros are kept --
        rain == 0.0 mm is a dry day, not missing data.
        """
        zone_path = f"{S.ZONES_PATH}/{zone_id}"
        sensors: List[FarmSensorAPI] = []
        for prim in self._stage.GetPrimAtPath(S.SENSORS_PATH).GetChildren():
            api = FarmSensorAPI.Get(prim)
            if api and zone_path in [str(t) for t in api.GetZoneRel().GetTargets()]:
                sensors.append(api)

        def mean(name: str) -> Optional[float]:
            vals: List[float] = []
            for api in sensors:
                attr = api.attr(name)
                if attr.HasAuthoredValue():
                    v = attr.Get()
                    if v is not None:
                        vals.append(float(v))
            return sum(vals) / len(vals) if vals else None

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
