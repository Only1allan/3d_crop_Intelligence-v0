"""
Headless tests for scan_io: 3DGS PLY -> UsdGeomPoints farm scan asset.

The fixture is a minimal but faithful binary_little_endian 3DGS PLY (the
INRIA property layout: x/y/z, normals, f_dc_0..2, f_rest_*, opacity,
scale_0..2, rot_0..3) with hand-computable values, so every conversion step
is asserted exactly.
"""
from __future__ import annotations

import math
import os
import struct
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.dirname(HERE)
if EXT_ROOT not in sys.path:
    sys.path.insert(0, EXT_ROOT)

pxr = pytest.importorskip("pxr")
from pxr import Sdf, Usd, UsdGeom  # noqa: E402

from omniverse_crop_intelligence import settings as S  # noqa: E402
from omniverse_crop_intelligence.scan_io import (  # noqa: E402
    SH_C0, convert, parse_ply_header)
from omniverse_crop_intelligence.stage_builder import StageBuilder  # noqa: E402

# INRIA 3DGS PLY property layout, in order — the exact 62-property schema the
# trainer emits (f_rest_0..44 full SH band included).
PROPS = ([("float", n) for n in ("x", "y", "z", "nx", "ny", "nz")]
         + [("float", f"f_dc_{i}") for i in range(3)]
         + [("float", f"f_rest_{i}") for i in range(45)]
         + [("float", "opacity")]
         + [("float", f"scale_{i}") for i in range(3)]
         + [("float", f"rot_{i}") for i in range(4)])


def _write_ply(path: str, rows) -> None:
    header = ["ply", "format binary_little_endian 1.0",
              f"element vertex {len(rows)}",
              *[f"property {t} {n}" for t, n in PROPS], "end_header", ""]
    with open(path, "wb") as fh:
        fh.write("\n".join(header).encode("ascii"))
        for row in rows:
            fh.write(struct.pack("<" + "f" * len(PROPS), *[float(v) for v in row]))


def _row(x, y, z, r, g, b, scale=math.log(0.05), idx=0):
    # f_dc_* chosen so 0.5 + SH_C0*f_dc == the target channel exactly.
    # f_rest_0..44 padded with a varied ramp: the parser must skip them by name.
    return (x, y, z, 0, 0, 0,
            (r - 0.5) / SH_C0, (g - 0.5) / SH_C0, (b - 0.5) / SH_C0,
            *[(idx + j) % 7 * 0.01 - 0.03 for j in range(45)],
            0.9, scale, scale, scale, 1, 0, 0, 0)


@pytest.fixture()
def ply(tmp_path):
    # 8 points, Y-up source frame (COLMAP convention), distinct colors.
    rows = [_row(1.0 * i, 0.5 * i, -0.25 * i, i / 8.0, 1.0 - i / 8.0, 0.5, idx=i) for i in range(8)]
    path = str(tmp_path / "scan.ply")
    _write_ply(path, rows)
    return path


def test_parse_header(ply):
    count, props, offset = parse_ply_header(ply)
    assert count == 8
    assert [n for _, n in props] == [n for _, n in PROPS]
    assert offset > 0 and os.path.getsize(ply) > offset


def test_ascii_ply_rejected(tmp_path):
    path = str(tmp_path / "ascii.ply")
    with open(path, "w") as fh:
        fh.write("ply\nformat ascii 1.0\nelement vertex 1\nproperty float x\nend_header\n0\n")
    with pytest.raises(ValueError, match="binary_little_endian"):
        parse_ply_header(path)


def test_convert_values_and_structure(ply, tmp_path):
    out = str(tmp_path / "farm_scan.usda")
    summary = convert(ply, out, prim_path="/FarmScan", source_up_axis="Y")
    assert summary["points_out"] == 8 and summary["stride"] == 1

    stage = Usd.Stage.Open(out)
    assert stage.GetDefaultPrim().GetPath() == Sdf.Path("/FarmScan")
    pts = UsdGeom.Points(stage.GetPrimAtPath("/FarmScan/PointCloud"))
    assert pts
    points = pts.GetPointsAttr().Get()
    assert len(points) == 8
    # Y-up source (x, y, z) -> Z-up stage (x, -z, y)
    assert points[3] == pytest.approx((3.0, 0.75, 1.5), abs=1e-6)
    color_pv = UsdGeom.PrimvarsAPI(pts.GetPrim()).GetPrimvar("displayColor")
    assert color_pv.GetInterpolation() == UsdGeom.Tokens.vertex
    colors = color_pv.Get()
    assert len(colors) == 8
    assert colors[2] == pytest.approx((0.25, 0.75, 0.5), abs=1e-6)
    widths_attr = pts.GetPrim().GetAttribute("widths")
    assert widths_attr and widths_attr.GetMetadata("interpolation") == UsdGeom.Tokens.vertex
    widths = widths_attr.Get()
    assert len(widths) == 8 and widths[0] == pytest.approx(0.05, abs=1e-6)
    extent = pts.GetExtentAttr().Get()
    assert extent[0] == pytest.approx((0.0, 0.0, 0.0), abs=1e-6)
    assert extent[1] == pytest.approx((7.0, 1.75, 3.5), abs=1e-6)


def test_convert_downsamples_and_keeps_axes(ply, tmp_path):
    out = str(tmp_path / "stride.usda")
    summary = convert(ply, out, max_points=4, author_widths=False, source_up_axis="Z")
    assert summary["stride"] == 2 and summary["points_out"] == 4 and summary["widths"] is False
    stage = Usd.Stage.Open(out)
    pts = UsdGeom.Points(stage.GetPrimAtPath("/FarmScan/PointCloud"))
    # source_up_axis="Z" keeps raw coordinates: (x, y, z) untouched.
    # stride 2 over rows 0..7 samples rows 0, 2, 4, 6 -> points[1] is row 2.
    assert pts.GetPointsAttr().Get()[1] == pytest.approx((2.0, 1.0, -0.5), abs=1e-6)
    assert not pts.GetPrim().GetAttribute("widths").HasAuthoredValue(), \
        "widths must be skipped with --no-widths"


def test_converted_scan_composes_into_the_twin(ply, tmp_path):
    """The real integration contract: StageBuilder references ./farm_scan.usda
    and the converted points appear under /World/Farm/FarmScan headless."""
    layers = str(tmp_path / "layers")
    os.makedirs(layers, exist_ok=True)
    convert(ply, os.path.join(layers, "farm_scan.usda"), source_up_axis="Y")
    stack = StageBuilder(layers).build(overwrite=True)
    scan = stack.stage.GetPrimAtPath(S.FARM_SCAN_PATH)
    assert scan
    points = UsdGeom.Points(scan.GetChild("PointCloud"))
    assert points and len(points.GetPointsAttr().Get()) == 8


def test_missing_property_is_actionable(tmp_path):
    path = str(tmp_path / "thin.ply")
    props = [("float", "x"), ("float", "y"), ("float", "z")]
    header = ["ply", "format binary_little_endian 1.0", "element vertex 1",
              *[f"property {t} {n}" for t, n in props], "end_header", ""]
    with open(path, "wb") as fh:
        fh.write("\n".join(header).encode("ascii"))
        fh.write(struct.pack("<fff", 0, 0, 0))
    out = str(tmp_path / "o.usda")
    with pytest.raises(ValueError, match="f_dc_0"):
        convert(path, out)
