#!/usr/bin/env python3
"""
Convert a 3D Gaussian-Splatting PLY into the farm scan USD asset.

    python tools/ply_to_usd_points.py --input scan.ply --out assets/layers/farm_scan.usda

Writes a self-contained .usda (UsdGeomPoints + displayColor + optional
widths) that ASS_LYR references via settings.DEFAULT_FARM_ASSET_PATH
("./farm_scan.usda"), so the scan composes with no Nucleus and no server.
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "exts", "omniverse_crop_intelligence"))

from omniverse_crop_intelligence.scan_io import convert  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="3DGS point_cloud.ply (binary_little_endian)")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "layers", "farm_scan.usda"),
                    help="output .usda (default: assets/layers/farm_scan.usda, next to the layers)")
    ap.add_argument("--prim", default="/FarmScan", help="root prim path inside the output layer")
    ap.add_argument("--max-points", type=int, default=0,
                    help="downsample to at most N points (uniform stride); 0 keeps all")
    ap.add_argument("--no-widths", action="store_true", help="skip per-point widths")
    ap.add_argument("--source-up-axis", choices=("Y", "Z"), default="Y",
                    help="frame of the source PLY: Y = COLMAP/3DGS default (mapped to the "
                         "stage's Z-up), Z = keep as-is")
    args = ap.parse_args()

    summary = convert(args.input, args.out, prim_path=args.prim,
                      max_points=args.max_points, author_widths=not args.no_widths,
                      source_up_axis=args.source_up_axis)
    print(f"ply      : {summary['ply']} ({summary['points_in']} gaussians)")
    print(f"usd      : {summary['usd']}")
    print(f"prim     : {summary['prim_path']}/PointCloud")
    print(f"points   : {summary['points_out']} (stride {summary['stride']}, widths={summary['widths']})")
    print("compose  : referenced by ASS_LYR as './farm_scan.usda' -> /World/Farm/FarmScan")
    return 0


if __name__ == "__main__":
    sys.exit(main())
