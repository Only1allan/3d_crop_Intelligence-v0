"""
Omniverse Crop Intelligence - agricultural digital twin Kit extension.

Package layout
    settings.py          constants: layer names, prim paths, schema tokens
    schema/              codeless FarmSensorAPI / FarmZoneAPI / CropModelStateAPI + wrappers
    stage_builder.py     generates ASS/DATA/SIM/RUNTIME sublayers + root stage (pxr only)
    sensor_manager.py    spawn zones / sensors into DATA_LYR (pxr only)
    phase2/              RuntimeWriter (functional) + ingestion / model bridge stubs
    ui/control_panel.py  omni.ui window (Kit only)
    extension.py         omni.ext.IExt entry point (Kit only)

The pxr-only modules are importable without Kit so `pytest tests/` runs in CI
with `pip install usd-core`.
"""
from . import settings  # noqa: F401

try:  # Kit runtime: expose the IExt subclass for the extension manager.
    from .extension import OmniverseCropIntelligenceExtension  # noqa: F401
except ImportError:  # headless: omni.* not available, pxr modules still usable.
    pass
