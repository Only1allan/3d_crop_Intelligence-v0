"""
StageBuilder: programmatic generation of the farm digital twin layer stack.

    farm_twin.usda            (root; only holds subLayers + stage metadata)
      +-- RUNTIME_LYR.usda    strongest  : live telemetry overrides (Phase 2)
      +-- SIM_LYR.usda                   : physics / collision (Isaac Sim, later)
      +-- DATA_LYR.usda                  : zones + sensor identity & placement
      +-- ASS_LYR.usda        weakest    : static 3D farm environment

Design rules enforced here
--------------------------
* The root layer never authors prims. Every opinion lives in exactly one
  sublayer, so `clear_runtime_layer()` can wipe live state without touching
  geometry or sensor definitions.
* ASS_LYR references the farm scan *by asset path*; it never copies geometry.
  If the reference cannot be resolved (no Nucleus, placeholder path) the
  PlaceholderGround mesh keeps the viewport non-empty and gives sensors a
  visual floor.
* This module imports only `pxr`, never `omni.*`, so it runs headless in CI
  with `usd-core`. extension.py is the only place that touches omni.usd.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, Vt

from . import settings as S
from .schema import register_schema_plugin


@dataclass
class LayerStack:
    """Resolved on-disk paths of the generated stack plus the composed stage."""
    output_dir: str
    root_path: str
    layer_paths: Dict[str, str] = field(default_factory=dict)  # file name -> absolute path
    stage: Optional[Usd.Stage] = None

    def layer(self, file_name: str) -> Sdf.Layer:
        return Sdf.Layer.FindOrOpen(self.layer_paths[file_name])

    @property
    def runtime_layer(self) -> Sdf.Layer:
        return self.layer(S.RUNTIME_LAYER_FILE)

    @property
    def data_layer(self) -> Sdf.Layer:
        return self.layer(S.DATA_LAYER_FILE)

    @property
    def asset_layer(self) -> Sdf.Layer:
        return self.layer(S.ASSET_LAYER_FILE)

    @property
    def sim_layer(self) -> Sdf.Layer:
        return self.layer(S.SIM_LAYER_FILE)


class StageBuilder:
    """Create (or re-open) the sublayer stack and the root stage."""

    def __init__(self, output_dir: str, farm_asset_path: str = S.DEFAULT_FARM_ASSET_PATH):
        self.output_dir = os.path.abspath(output_dir)
        self.farm_asset_path = farm_asset_path

    # ------------------------------------------------------------------ public
    def build(self, overwrite: bool = False) -> LayerStack:
        """
        Generate every layer file and return an opened root stage.

        overwrite=False keeps existing DATA/RUNTIME content (so re-running the
        extension does not wipe sensors a user placed); ASS_LYR is always
        re-authored because it is a pure function of the asset path.
        """
        register_schema_plugin()
        os.makedirs(self.output_dir, exist_ok=True)

        paths = {name: os.path.join(self.output_dir, name)
                 for name in (S.ROOT_LAYER_FILE,) + S.SUBLAYER_ORDER_STRONGEST_FIRST}

        self._author_asset_layer(paths[S.ASSET_LAYER_FILE])
        self._author_or_keep(paths[S.DATA_LAYER_FILE], self._author_data_layer, overwrite)
        self._author_or_keep(paths[S.SIM_LAYER_FILE], self._author_sim_layer, overwrite)
        self._author_or_keep(paths[S.RUNTIME_LAYER_FILE], self._author_runtime_layer, overwrite)
        self._author_root_layer(paths[S.ROOT_LAYER_FILE])

        stage = Usd.Stage.Open(paths[S.ROOT_LAYER_FILE])
        stack = LayerStack(self.output_dir, paths[S.ROOT_LAYER_FILE], paths, stage)
        self.validate(stack)
        return stack

    @staticmethod
    def validate(stack: LayerStack) -> List[str]:
        """Assert the invariants Phase 2 will depend on. Returns problems (empty == ok)."""
        problems: List[str] = []
        root = stack.stage.GetRootLayer()
        expected = [f"./{n}" for n in S.SUBLAYER_ORDER_STRONGEST_FIRST]
        if list(root.subLayerPaths) != expected:
            problems.append(f"subLayers order is {list(root.subLayerPaths)}, expected {expected}")
        if root.rootPrims:
            problems.append("root layer must not author prims")
        if stack.stage.GetDefaultPrim().GetPath() != Sdf.Path(S.WORLD_PATH):
            problems.append("defaultPrim must be /World")
        if UsdGeom.GetStageUpAxis(stack.stage) != S.STAGE_UP_AXIS:
            problems.append("stage upAxis must be Z")
        for p in (S.FARM_SCAN_PATH, S.SENSORS_PATH, S.ZONES_PATH):
            if not stack.stage.GetPrimAtPath(p):
                problems.append(f"missing prim {p}")
        if problems:
            raise RuntimeError("Layer stack validation failed: " + "; ".join(problems))
        return problems

    @staticmethod
    def clear_runtime_layer(stack: LayerStack) -> None:
        """Drop every live override; the stage reverts to DATA + ASSET opinions."""
        layer = stack.runtime_layer
        layer.Clear()
        StageBuilder._stamp(layer, "RUNTIME layer - live telemetry overrides (cleared)")
        layer.Save()

    @staticmethod
    def save_all(stack: LayerStack) -> None:
        for name in stack.layer_paths:
            lyr = Sdf.Layer.FindOrOpen(stack.layer_paths[name])
            if lyr and lyr.dirty:
                lyr.Save()

    # --------------------------------------------------------------- authoring
    @staticmethod
    def _author_or_keep(path: str, author_fn, overwrite: bool) -> None:
        if os.path.exists(path) and not overwrite:
            return
        author_fn(path)

    @staticmethod
    def _stamp(layer: Sdf.Layer, comment: str) -> None:
        layer.comment = comment
        layer.customLayerData = {
            "generator": S.EXTENSION_NAME,
            "phase": "1",
        }

    def _new_layer(self, path: str, comment: str) -> Sdf.Layer:
        """
        Create a fresh layer at `path`. If the layer is already open in this
        process (a previous build, or the stage currently open in Kit) we
        clear and reuse that handle: Sdf.Layer.CreateNew refuses duplicate
        identifiers, and reusing keeps an open stage's composition live.
        """
        layer = Sdf.Layer.Find(path)
        if layer:
            layer.Clear()
        else:
            if os.path.exists(path):
                os.remove(path)
            layer = Sdf.Layer.CreateNew(path)
        self._stamp(layer, comment)
        return layer

    def _author_root_layer(self, path: str) -> None:
        layer = self._new_layer(path, "Farm digital twin root. Holds ONLY the sublayer stack; never author prims here.")
        # Relative paths keep the folder relocatable (copy to Nucleus as a unit).
        layer.subLayerPaths = [f"./{n}" for n in S.SUBLAYER_ORDER_STRONGEST_FIRST]
        stage = Usd.Stage.Open(layer)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, S.STAGE_METERS_PER_UNIT)
        stage.SetDefaultPrim(stage.GetPrimAtPath(S.WORLD_PATH))
        layer.Save()

    def _author_asset_layer(self, path: str) -> None:
        layer = self._new_layer(path, "ASSET layer - static 3D farm environment. Re-generated on every build.")
        stage = Usd.Stage.Open(layer)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, S.STAGE_METERS_PER_UNIT)

        world = UsdGeom.Xform.Define(stage, S.WORLD_PATH)
        stage.SetDefaultPrim(world.GetPrim())
        UsdGeom.Xform.Define(stage, S.FARM_PATH)

        # The 3D farm scan (3DGS-derived USD, photogrammetry mesh, ...). We
        # reference rather than payload so the scan composes eagerly for the
        # viewer; switch to AddPayload() once scans exceed a few hundred MB.
        scan = UsdGeom.Xform.Define(stage, S.FARM_SCAN_PATH)
        scan.GetPrim().GetReferences().AddReference(self.farm_asset_path)
        scan.GetPrim().SetMetadata("comment",
            "3D farm scan. Expected upstream pipeline: photos -> 3DGS (.ply) -> USD. "
            "If the asset cannot be resolved the prim composes empty and PlaceholderGround is shown.")
        scan.GetPrim().CreateAttribute("farm:assetPath", Sdf.ValueTypeNames.String, custom=True).Set(self.farm_asset_path)

        self._author_placeholder_ground(stage)

        UsdGeom.Xform.Define(stage, S.ENVIRONMENT_PATH)
        sun = UsdLux.DistantLight.Define(stage, S.SUN_LIGHT_PATH)
        sun.CreateIntensityAttr(3000.0)
        sun.CreateAngleAttr(0.53)
        # Rotate so the light comes from above-ish for a Z-up stage.
        UsdGeom.Xformable(sun).AddRotateXYZOp().Set(Gf.Vec3f(-50.0, 0.0, 30.0))

        layer.Save()

    def _author_placeholder_ground(self, stage: Usd.Stage) -> None:
        half = S.PLACEHOLDER_GROUND_SIZE_M / 2.0
        mesh = UsdGeom.Mesh.Define(stage, S.PLACEHOLDER_GROUND_PATH)
        mesh.CreatePointsAttr(Vt.Vec3fArray([
            Gf.Vec3f(-half, -half, 0), Gf.Vec3f(half, -half, 0),
            Gf.Vec3f(half, half, 0), Gf.Vec3f(-half, half, 0)]))
        mesh.CreateFaceVertexCountsAttr(Vt.IntArray([4]))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray([0, 1, 2, 3]))
        mesh.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(-half, -half, 0), Gf.Vec3f(half, half, 0)]))
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.30, 0.24, 0.16)]))
        mesh.CreateDoubleSidedAttr(True)
        mesh.GetPrim().SetMetadata("comment",
            "Fallback soil plane so the viewer is never empty. Hide or delete once the real scan resolves.")

    def _author_data_layer(self, path: str) -> None:
        layer = self._new_layer(path, "DATA layer - semantic definitions: zones, sensor identity and 3D placement.")
        stage = Usd.Stage.Open(layer)
        UsdGeom.Xform.Define(stage, S.WORLD_PATH)
        zones = UsdGeom.Scope.Define(stage, S.ZONES_PATH)
        zones.GetPrim().SetMetadata("comment", "One FarmZoneAPI Xform per plot / assessment site.")
        sensors = UsdGeom.Scope.Define(stage, S.SENSORS_PATH)
        sensors.GetPrim().SetMetadata("comment", "One FarmSensorAPI Xform per sensing point. Transform = stage-local metres.")
        layer.Save()

    def _author_sim_layer(self, path: str) -> None:
        layer = self._new_layer(path, "SIM layer - reserved for PhysX collision meshes and Isaac Sim robot assets (Phase 3).")
        stage = Usd.Stage.Open(layer)
        UsdGeom.Xform.Define(stage, S.WORLD_PATH)
        sim = UsdGeom.Scope.Define(stage, S.SIMULATION_PATH)
        sim.GetPrim().SetMetadata("comment",
            "Phase 3: author UsdPhysics collision APIs on /World/Farm/* as `over` prims here; "
            "never in ASS_LYR so scans stay pristine.")
        layer.Save()

    def _author_runtime_layer(self, path: str) -> None:
        layer = self._new_layer(path, "RUNTIME layer - live telemetry overrides. Cleared freely; never holds definitions.")
        layer.Save()
