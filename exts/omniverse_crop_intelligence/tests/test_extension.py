"""
In-Kit tests (omni.kit.test). Run with:

    kit --ext-folder ./exts --enable omniverse_crop_intelligence \
        --exec "omni.kit.test" --/exts/omni.kit.test/testExtension=omniverse_crop_intelligence

or via the Kit App Template `repo test` flow. Headless USD invariants are in
test_headless.py; this file only checks the Kit glue.
"""
import os
import tempfile

import omni.kit.test
import omni.ui as ui
import omni.usd

from omniverse_crop_intelligence import settings as S
from omniverse_crop_intelligence.extension import get_instance


class TestCropIntelligenceExtension(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self.ext = get_instance()
        self.assertIsNotNone(self.ext, "extension instance not registered")
        self.tmp = tempfile.mkdtemp(prefix="farm_twin_")
        self.ext.layer_output_dir = self.tmp

    async def test_window_exists(self):
        self.assertIsNotNone(ui.Workspace.get_window(S.WINDOW_TITLE))

    async def test_build_stage_and_spawn_sensors(self):
        msg = self.ext.build_stage(overwrite=True)
        self.assertIn("Stage built", msg)
        stage = omni.usd.get_context().get_stage()
        self.assertTrue(stage.GetPrimAtPath(S.FARM_SCAN_PATH))
        self.assertEqual(len(self.ext.sensor_summary()), 3)
        for name in S.SUBLAYER_ORDER_STRONGEST_FIRST:
            self.assertTrue(os.path.isfile(os.path.join(self.tmp, name)), name)

    async def test_runtime_tick_and_clear(self):
        self.ext.build_stage(overwrite=True)
        self.ext.simulate_telemetry_tick()
        rows = self.ext.sensor_summary()
        self.assertTrue(all(r["lastUpdateTime"] > 0 for r in rows))
        self.ext.clear_runtime_layer()
        rows = self.ext.sensor_summary()
        self.assertTrue(all(r["soilMoisture"] == 0.0 for r in rows))
