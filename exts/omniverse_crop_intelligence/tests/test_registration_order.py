"""
Registration-order regression tests (fresh subprocesses: SchemaRegistry state
is process-global, so these cannot run in-process).

Platform facts pinned here (verified on usd-core 26.8):
  * importing `omniverse_crop_intelligence.schema` registers the codeless
    plugin and FarmSensorAPI applies, even if `pxr` was imported first;
  * if a stage was opened BEFORE the first registration, the first plugin
    notice can be missed while the registry builds lazily - a repeat
    registration attempt makes it rebuild, so register_schema_plugin()
    recovers via bounded retries.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.dirname(HERE)
pytest.importorskip("pxr")


def _run(code: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = EXT_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)


def test_package_import_registers_schema_before_any_pxr_use():
    res = _run(
        "import pxr\n"
        "import omniverse_crop_intelligence.schema as S\n"
        "from pxr import Usd, UsdGeom\n"
        "assert Usd.SchemaRegistry().FindAppliedAPIPrimDefinition('FarmSensorAPI'), 'not registered'\n"
        "stage = Usd.Stage.CreateInMemory()\n"
        "prim = UsdGeom.Xform.Define(stage, '/S').GetPrim()\n"
        "assert prim.ApplyAPI('FarmSensorAPI')\n"
        "assert prim.HasAttribute('farmSensor:soilMoisture')\n"
        "print('OK')\n"
    )
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout


def test_stage_before_registration_recovers_on_retry():
    """A process that opened a stage before the first registration must still
    recover: a repeat RegisterPlugins makes the SchemaRegistry rebuild."""
    res = _run(
        "import tempfile, os\n"
        "from pxr import Sdf, Usd, UsdGeom\n"
        "lyr = Sdf.Layer.CreateNew(os.path.join(tempfile.mkdtemp(), 'a.usda'))\n"
        "Usd.Stage.Open(lyr)  # initializes SchemaRegistry without our plugin\n"
        "import omniverse_crop_intelligence.schema as S\n"
        "assert S.register_schema_plugin() is True, 'retry must recover'\n"
        "stage = Usd.Stage.CreateInMemory()\n"
        "prim = UsdGeom.Xform.Define(stage, '/S').GetPrim()\n"
        "assert prim.ApplyAPI('FarmSensorAPI') and prim.HasAttribute('farmSensor:soilMoisture')\n"
        "print('OK')\n"
    )
    assert res.returncode == 0, res.stderr
    assert "OK" in res.stdout
