"""
PHASE 2 STUB - live telemetry ingestion (AWS IoT Core -> RUNTIME_LYR).

Nothing in this file opens a socket. It fixes the *shape* of the ingestion
loop so Phase 2 can fill in the transport without touching the scene code.

Target architecture (AWS, replacing the Azure IoT Operations reference in the
blueprint PDF):

    field sensors --MQTT--> AWS IoT Core (topic: farm/<farmId>/sensor/<sensorId>/telemetry)
                             |-- IoT Rule -> Kinesis Data Stream (fan-out, replay)
                             |-- IoT Rule -> Timestream (history for SUBSTOR daily aggregation)
    Kit extension  <--MQTT over WebSocket (SigV4)-- IoT Core   [this module]

Legacy back-fills (batch, not MQTT):
    * AgriFusion Aurora `assessments` rows  -> assessment_virtual sensors (soil chemistry)
    * FarmWise Neo4j `DailySnapshot` nodes -> weather_station / satellite_virtual updates
    Both go through the same `TelemetryMessage` -> RuntimeWriter path so the
    scene never knows which upstream produced a value.

Threading contract:
    The MQTT client callback runs on its own thread. USD is NOT thread-safe
    for writes. Callbacks must only `queue.put()`; `pump()` is called from
    Kit's update loop (omni.kit.app update event) and performs the writes.
"""
from __future__ import annotations

import queue
from dataclasses import dataclass, field
from typing import Dict, Optional

from .runtime_writer import RuntimeWriter


@dataclass
class TelemetryMessage:
    """Normalised payload. Keys in `values` are FarmSensorAPI short names."""
    sensor_id: str
    values: Dict[str, float]
    timestamp: float
    source: str = "aws_iot_core"
    zone_id: Optional[str] = None
    zone_values: Dict[str, object] = field(default_factory=dict)


class TelemetryIngestor:
    """
    Skeleton of the Phase 2 ingestion loop.

    Lifecycle:   start() -> [transport thread enqueues] -> pump() per frame -> stop()
    """

    def __init__(self, writer: RuntimeWriter, max_batch_per_frame: int = 256):
        self._writer = writer
        self._queue: "queue.Queue[TelemetryMessage]" = queue.Queue()
        self._max_batch = max_batch_per_frame
        self._running = False

    # ---- transport (Phase 2 fills these) ------------------------------------
    def start(self) -> None:
        """
        TODO(Phase 2): create the AWS IoT Core MQTT-over-WebSocket client
        (awsiotsdk / awscrt), subscribe to farm/+/sensor/+/telemetry, and set
        the on_message callback to `self.enqueue_raw`. Credentials come from
        carb settings / env (never hard-coded). No network code in Phase 1.
        """
        self._running = True

    def stop(self) -> None:
        """TODO(Phase 2): disconnect the MQTT client and drain the queue."""
        self._running = False

    def enqueue_raw(self, topic: str, payload: bytes) -> None:
        """
        TODO(Phase 2): parse the JSON payload, map device field names to
        FarmSensorAPI names (see docs/01_REPOSITORY_ANALYSIS_AND_MAPPING.md
        section 5), convert units, and `self._queue.put(TelemetryMessage(...))`.
        Runs on the transport thread: NO USD calls here.
        """
        raise NotImplementedError("Phase 2: payload parsing")

    def enqueue(self, msg: TelemetryMessage) -> None:
        """Thread-safe hand-off used by tests and by legacy back-fill jobs."""
        self._queue.put(msg)

    # ---- main-thread side ---------------------------------------------------
    def pump(self) -> int:
        """
        Drain up to `max_batch_per_frame` messages and write them to RUNTIME_LYR.
        Called from the Kit update loop. Each write is an attribute override in
        the runtime layer, so the viewport updates without any stage reload.
        Returns the number of messages applied.
        """
        applied = 0
        while applied < self._max_batch:
            try:
                msg = self._queue.get_nowait()
            except queue.Empty:
                break
            self._writer.write_sensor(msg.sensor_id, msg.values, timestamp=msg.timestamp)
            if msg.zone_id and msg.zone_values:
                self._writer.write_zone(msg.zone_id, msg.zone_values, timestamp=msg.timestamp)
            applied += 1
        return applied

    @property
    def pending(self) -> int:
        return self._queue.qsize()
