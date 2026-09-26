#!/usr/bin/env python3
"""
Generate the farm layer stack without Omniverse Kit (pure usd-core).

    python tools/build_layers_headless.py --out assets/layers --demo
    usdview assets/layers/farm_twin.usda        # if you have usdview

Useful for CI, for inspecting the .usda text, and for handing the folder to
someone who will open it in USD Composer / Isaac Sim.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "exts", "omniverse_crop_intelligence"))

from omniverse_crop_intelligence import settings as S  # noqa: E402
from omniverse_crop_intelligence.sensor_manager import SensorManager  # noqa: E402
from omniverse_crop_intelligence.stage_builder import StageBuilder  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "layers"))
    ap.add_argument("--asset", default=S.DEFAULT_FARM_ASSET_PATH, help="farm scan asset path to reference")
    ap.add_argument("--demo", action="store_true", help="spawn the demo zone + 3 test sensors with seeded values")
    ap.add_argument("--overwrite", action="store_true", help="wipe DATA/RUNTIME layers")
    args = ap.parse_args()

    stack = StageBuilder(args.out, args.asset).build(overwrite=args.overwrite)
    if args.demo:
        SensorManager(stack).spawn_test_sensors(seed_runtime_values=True)
    StageBuilder.save_all(stack)

    print(f"root: {stack.root_path}")
    print("sublayers (strongest first):")
    for p in stack.stage.GetRootLayer().subLayerPaths:
        print(f"  {p}")
    sensors = SensorManager(stack).sensor_summary()
    print(f"sensors: {len(sensors)}")
    for s in sensors:
        print(f"  {s['id']:<20} {s['kind']:<18} {s['status']:<8} pos={s['position']} moisture={s['soilMoisture']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
