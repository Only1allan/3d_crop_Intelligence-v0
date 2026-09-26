"""
PHASE 2 STUB - SimCast late blight forecast bridge.

Scope guard: blight-unit and fungicide-unit tables are NOT implemented here.
This module only defines how SimCast will read from and write to the stage.

FarmWise (`agriLegends`) has no SimCast: its disease logic is five threshold
rules on daily precipitation/temperature plus an LLM. Its `daily_avg_humidity`
is a single afternoon value, which is insufficient: SimCast needs, per day,
the number of consecutive hours with RH >= 90 % and the mean temperature
during those hours. Those are exactly `farmSensor:humidHours` and
`farmSensor:humidPeriodTemperature`, which Phase 2 IoT weather stations will
supply (or an edge aggregator will compute from hourly RH/T).

    inputs per zone (daily)   FarmSensorAPI on weather_station / canopy_probe sensors
      humidHours, humidPeriodTemperature, precipitation (fungicide wash-off)
    inputs per zone (static)  FarmZoneAPI.variety -> cultivar resistance class
                              (FarmWise PotatoVariety.blightResistance: low / medium)
    outputs per zone          CropModelStateAPI via RuntimeWriter
      simcastBlightUnits, simcastFungicideUnits, simcastBlightRisk,
      simcastSprayRecommended, simcastLastRunTime
    visual feedback           farmSensor:status = "critical" on the zone's canopy
                              sensors -> RuntimeWriter recolours their markers.
                              Later: colour override on the 3DGS canopy zone prim.
"""
from __future__ import annotations

from dataclasses import dataclass

from pxr import Usd

from .runtime_writer import RuntimeWriter


@dataclass
class SimcastDailyInput:
    zone_id: str
    date: str
    humid_hours: float                 # hours with RH >= 90 %
    humid_period_temperature: float    # degC mean over those hours
    precipitation: float               # mm (fungicide weathering)
    resistance_class: str              # "susceptible" | "moderately_susceptible" | "moderately_resistant"


class SimcastBridge:
    def __init__(self, stage: Usd.Stage, writer: RuntimeWriter):
        self._stage = stage
        self._writer = writer

    async def run_daily(self, zone_id: str, date: str) -> None:
        """
        TODO(Phase 2):
          1. gather SimcastDailyInput from the zone's weather sensors (see SubstorBridge.collect_daily_input for the pattern)
          2. out = simcast_service.accumulate(inp)   (blight units + fungicide units since last spray)
          3. self._writer.write_model_state(zone_id, {"simcastBlightUnits": ..., "simcastBlightRisk": ..., ...})
          4. if out.risk in ("high", "severe"): mark zone sensors status="critical" via write_sensor
        """
        raise NotImplementedError("Phase 2: SimCast runs as an external service")
