"""Codeless OpenUSD schema plugin + thin Python wrappers.

Importing this package REGISTERS the schema plugin immediately (see
register_schema_plugin): on usd-core 26.8 a plugin registered AFTER the
process's first SchemaRegistry use (any stage open / registry query) never
propagates, so registration must happen before any other pxr work. Importing
this package first guarantees that ordering for every consumer (Kit, tools,
notebooks, Phase 2 adapters).
"""
from .register import register_schema_plugin, is_schema_registered, SCHEMA_PLUGIN_DIR  # noqa: F401
from .farm_sensor_api import FarmSensorAPI, FarmZoneAPI, CropModelStateAPI  # noqa: F401

try:  # import-time registration; never breaks the import itself
    register_schema_plugin()
except Exception:  # pragma: no cover - late import into a live registry; build() re-checks
    pass
