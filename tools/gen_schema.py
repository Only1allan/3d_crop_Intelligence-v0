#!/usr/bin/env python3
"""
Regenerate the codeless schema plugin from schema.usda.

    python tools/gen_schema.py            # uses the interpreter's pxr (pip install usd-core jinja2)

Runs usdGenSchema (shipped inside the pxr package) and patches the
@PLUG_INFO_*@ placeholders so the plugin loads from its own folder.
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT, "exts", "omniverse_crop_intelligence", "omniverse_crop_intelligence", "schema", "farmSensor")


def main() -> int:
    try:
        import pxr  # noqa: F401
        from pxr import Usd
    except ImportError:
        print("pxr not importable. `pip install -r requirements-dev.txt` first.", file=sys.stderr)
        return 2
    gen = os.path.join(os.path.dirname(Usd.__file__), "usdGenSchema.py")
    if not os.path.isfile(gen):
        print(f"usdGenSchema.py not found next to {Usd.__file__}", file=sys.stderr)
        return 2

    schema = os.path.join(SCHEMA_DIR, "schema.usda")
    print(f"usdGenSchema {schema} -> {SCHEMA_DIR}")
    res = subprocess.run([sys.executable, gen, schema, SCHEMA_DIR], cwd=SCHEMA_DIR)
    if res.returncode != 0:
        return res.returncode

    plug = os.path.join(SCHEMA_DIR, "plugInfo.json")
    text = open(plug).read()
    text = (text.replace('"@PLUG_INFO_LIBRARY_PATH@"', '""')
                .replace('"@PLUG_INFO_RESOURCE_PATH@"', '"."')
                .replace('"@PLUG_INFO_ROOT@"', '"."'))
    open(plug, "w").write(text)
    print("patched plugInfo.json placeholders")

    # Smoke test: register and apply.
    sys.path.insert(0, os.path.join(ROOT, "exts", "omniverse_crop_intelligence"))
    from omniverse_crop_intelligence.schema import register_schema_plugin
    from pxr import Usd, UsdGeom
    register_schema_plugin(SCHEMA_DIR)
    stage = Usd.Stage.CreateInMemory()
    prim = UsdGeom.Xform.Define(stage, "/S").GetPrim()
    assert prim.ApplyAPI("FarmSensorAPI") and prim.HasAttribute("farmSensor:soilMoisture")
    print("OK: FarmSensorAPI applies with typed attributes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
