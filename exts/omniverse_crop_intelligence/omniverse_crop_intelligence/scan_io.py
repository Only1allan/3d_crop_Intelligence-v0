"""
scan_io: convert a 3D Gaussian-Splatting PLY into a USD UsdGeomPoints asset.

Pipeline position (docs/04, decision D3):

    photos -> 3DGS training (Colab T4) -> point_cloud.ply -> scan_io -> farm_scan.usda

ASS_LYR references "./farm_scan.usda" (see settings.DEFAULT_FARM_ASSET_PATH),
so the converted point cloud composes under /World/Farm/FarmScan with zero
infrastructure: no Nucleus, no unverified USD splat format. The 3DGS PLY is
the standard INRIA binary_little_endian layout; color comes from the zeroth
spherical-harmonics band (SH_C0 * f_dc + 0.5), optional point widths from the
log-space scales.

Pure pxr + stdlib; numpy is an optional fast path, never a requirement.
"""
from __future__ import annotations

import math
import os
import struct
from typing import Dict, List, Optional, Sequence, Tuple

from pxr import Gf, Sdf, Usd, UsdGeom, Vt

SH_C0 = 0.28209479177387814  # 3DGS paper: rgb = 0.5 + C0 * sh0

_PLY_TYPE_FMT = {
    "float": "<f", "float32": "<f",
    "double": "<d", "float64": "<d",
    "uchar": "<B", "uint8": "<B",
    "char": "<b", "int8": "<b",
    "int": "<i", "int32": "<i",
    "uint": "<I", "uint32": "<I",
    "short": "<h", "int16": "<h",
    "ushort": "<H", "uint16": "<H",
}
_PLY_TYPE_SIZE = {"<f": 4, "<d": 8, "<B": 1, "<b": 1, "<i": 4, "<I": 4, "<h": 2, "<H": 2}

Prop = Tuple[str, str]  # (ply_type, name)


def parse_ply_header(path: str) -> Tuple[int, List[Prop], int]:
    """
    Return (vertex_count, properties, data_offset) for a binary_little_endian
    PLY. Raises ValueError with an actionable message for ascii/big-endian
    files (3DGS trainers emit binary LE; that is the only thing we accept).
    """
    with open(path, "rb") as fh:
        head = fh.read(65536)
    end = head.find(b"end_header")
    if end == -1:
        raise ValueError("not a valid PLY: no end_header found in first 64 KiB")
    data_offset = end + len(b"end_header\n")
    if head[data_offset - 1:data_offset] != b"\n":
        # tolerate \r\n line endings
        data_offset = head.find(b"\n", end) + 1

    count = 0
    props: List[Prop] = []
    fmt_ok = False
    for raw in head[:end].split(b"\n"):
        line = raw.strip().decode("ascii", "replace")
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "format":
            if len(parts) < 3 or parts[1] != "binary_little_endian":
                raise ValueError(
                    f"unsupported PLY format '{' '.join(parts[1:])}': "
                    "scan_io needs binary_little_endian (3DGS trainers emit this)")
            fmt_ok = True
        elif parts[0] == "element":
            if len(parts) >= 3 and parts[1] != "vertex":
                raise ValueError(f"unsupported extra element '{parts[1]}': only 'vertex' PLYs supported")
            if len(parts) >= 3:
                count = int(parts[2])
        elif parts[0] == "property" and len(parts) >= 3:
            props.append((parts[1], parts[2]))
    if not fmt_ok:
        raise ValueError("PLY header has no 'format binary_little_endian' line")
    if not props:
        raise ValueError("PLY header declares no vertex properties")
    return count, props, data_offset


def _load_columns(path: str, offset: int, count: int, props: List[Prop],
                  wanted: Sequence[str]) -> Dict[str, List[float]]:
    """Read the named columns from the fixed-stride vertex block."""
    fmts = [_PLY_TYPE_FMT[t] for t, _ in props]
    stride = sum(_PLY_TYPE_SIZE[f] for f in fmts)
    row = struct.Struct("<" + "".join(f.lstrip("<") for f in fmts))
    idx = {name: i for i, (_, name) in enumerate(props)}
    missing = [w for w in wanted if w not in idx]
    if missing:
        raise ValueError(f"PLY is missing required properties: {missing}")

    out: Dict[str, List[float]] = {w: [] for w in wanted}
    with open(path, "rb") as fh:
        fh.seek(offset)
        blob = fh.read(count * stride)
    if len(blob) < count * stride:
        raise ValueError(f"truncated PLY vertex block: {len(blob)} bytes, expected {count * stride}")
    try:  # optional fast path
        import numpy as np  # type: ignore

        dtype = np.dtype([(name, ("f4" if _PLY_TYPE_SIZE[f] == 4 else "f8"))
                          for f, name in props])
        arr = np.frombuffer(blob, dtype=dtype, count=count)
        return {w: arr[w].astype("float64").tolist() for w in wanted}
    except ImportError:
        pass
    for r in range(count):
        vals = row.unpack_from(blob, r * stride)
        for w in wanted:
            out[w].append(float(vals[idx[w]]))
    return out


def _to_stage_frame(x: float, y: float, z: float, source_up_axis: str) -> Tuple[float, float, float]:
    """Map source coordinates into the twin's Z-up metres frame."""
    if source_up_axis == "Z":
        return x, y, z
    if source_up_axis == "Y":
        # COLMAP / 3DGS world (y roughly up after gauge fixing) -> Z-up stage.
        return x, -z, y
    raise ValueError(f"unsupported source_up_axis {source_up_axis!r} (use 'Y' or 'Z')")


def convert(ply_path: str, usd_path: str, prim_path: str = "/FarmScan",
            max_points: int = 0, author_widths: bool = True,
            source_up_axis: str = "Y") -> Dict[str, object]:
    """
    Convert a 3DGS PLY to a self-contained USDA layer holding one UsdGeomPoints
    prim (`prim_path`/PointCloud, with `prim_path` as defaultPrim so ASS_LYR's
    asset-path reference composes it). Returns a summary dict.
    """
    count, props, offset = parse_ply_header(ply_path)
    prop_names = {name for _, name in props}
    need = ["x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2"]
    scale_names = [f"scale_{i}" for i in range(3)]
    with_widths = author_widths and all(n in prop_names for n in scale_names)
    cols = _load_columns(ply_path, offset, count, props, need + (scale_names if with_widths else []))

    stride = 1
    if max_points and count > max_points:
        stride = math.ceil(count / max_points)
    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []
    cr: List[float] = []
    cg: List[float] = []
    cb: List[float] = []
    ws: List[float] = []
    for i in range(0, count, stride):
        px, py, pz = _to_stage_frame(cols["x"][i], cols["y"][i], cols["z"][i], source_up_axis)
        xs.append(px); ys.append(py); zs.append(pz)
        cr.append(min(1.0, max(0.0, 0.5 + SH_C0 * cols["f_dc_0"][i])))
        cg.append(min(1.0, max(0.0, 0.5 + SH_C0 * cols["f_dc_1"][i])))
        cb.append(min(1.0, max(0.0, 0.5 + SH_C0 * cols["f_dc_2"][i])))
        if with_widths:
            w = math.exp((cols["scale_0"][i] + cols["scale_1"][i] + cols["scale_2"][i]) / 3.0)
            ws.append(min(0.25, max(0.005, w)))
    n_out = len(xs)

    layer = Sdf.Layer.Find(usd_path)
    if layer:
        layer.Clear()
    else:
        if os.path.exists(usd_path):
            os.remove(usd_path)
        layer = Sdf.Layer.CreateNew(usd_path)
    stage = Usd.Stage.Open(layer)

    root = UsdGeom.Xform.Define(stage, prim_path)
    stage.SetDefaultPrim(root.GetPrim())
    root.GetPrim().SetMetadata("comment",
        "3DGS-derived point cloud. Source pipeline: photos -> 3DGS (.ply) -> scan_io -> USDA.")

    points = UsdGeom.Points.Define(stage, prim_path + "/PointCloud")
    points.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(xs[i], ys[i], zs[i]) for i in range(n_out)]))
    primvars = UsdGeom.PrimvarsAPI(points.GetPrim())
    color_pv = primvars.CreatePrimvar("displayColor", Sdf.ValueTypeNames.Color3fArray,
                                      UsdGeom.Tokens.vertex)
    color_pv.Set(Vt.Vec3fArray([Gf.Vec3f(cr[i], cg[i], cb[i]) for i in range(n_out)]))
    if with_widths:
        # `widths` is a built-in UsdGeom point attribute (NOT a primvar name):
        # author it directly with vertex interpolation for Hydra point sizing.
        w_attr = points.GetPrim().CreateAttribute("widths", Sdf.ValueTypeNames.FloatArray)
        w_attr.Set(Vt.FloatArray(ws))
        w_attr.SetMetadata("interpolation", UsdGeom.Tokens.vertex)
    lo = Gf.Vec3f(min(xs), min(ys), min(zs))
    hi = Gf.Vec3f(max(xs), max(ys), max(zs))
    points.CreateExtentAttr(Vt.Vec3fArray([lo, hi]))

    layer.customLayerData = {
        "generator": "scan_io (omniverse_crop_intelligence)",
        "sourcePly": os.path.basename(ply_path),
        "pointsIn": str(count),
        "pointsOut": str(n_out),
        "stride": str(stride),
        "sourceUpAxis": source_up_axis,
    }
    layer.Save()

    return {
        "ply": ply_path, "usd": usd_path, "prim_path": prim_path,
        "points_in": count, "points_out": n_out, "stride": stride,
        "widths": bool(with_widths),
    }
