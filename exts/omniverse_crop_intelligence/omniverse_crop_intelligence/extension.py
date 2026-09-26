"""
Kit extension entry point: omni.ext.IExt implementation and the controller
the control-panel window talks to.

Responsibilities (Phase 1):
  * register the codeless schema plugin on startup
  * build / open the farm layer stack through omni.usd
  * own SensorManager + RuntimeWriter for the open stage
  * expose the omni.ui window + Window menu entry

Everything USD-shaped is delegated to stage_builder / sensor_manager /
phase2.runtime_writer so this file stays thin and Kit-specific.
"""
from __future__ import annotations

import os
import random
import time
from typing import Dict, List, Optional, Tuple

import carb
import carb.settings
import carb.tokens
import omni.ext
import omni.kit.app
import omni.ui as ui
import omni.usd
from pxr import Sdf, Usd

from . import settings as S
from .phase2.runtime_writer import RuntimeWriter
from .schema import register_schema_plugin
from .sensor_manager import SensorManager, SensorSpec
from .stage_builder import LayerStack, StageBuilder
from .ui.control_panel import ControlPanelWindow

_instance: Optional["OmniverseCropIntelligenceExtension"] = None


def get_instance() -> Optional["OmniverseCropIntelligenceExtension"]:
    """Used by tests and by future extensions that want the live stack."""
    return _instance


class OmniverseCropIntelligenceExtension(omni.ext.IExt):
    # ------------------------------------------------------------- lifecycle
    def on_startup(self, ext_id: str) -> None:
        global _instance
        _instance = self
        self._ext_id = ext_id
        self._settings = carb.settings.get_settings()
        self._stack: Optional[LayerStack] = None
        self._sensors: Optional[SensorManager] = None
        self._writer: Optional[RuntimeWriter] = None
        self._menu = None

        self.farm_asset_path: str = self._settings.get(S.SETTING_FARM_ASSET_PATH) or S.DEFAULT_FARM_ASSET_PATH
        self.layer_output_dir: str = self._resolve_output_dir(self._settings.get(S.SETTING_LAYER_OUTPUT_DIR))

        register_schema_plugin()
        carb.log_info(f"[{S.EXTENSION_NAME}] FarmSensorAPI schema registered")

        self._window = ControlPanelWindow(self)
        ui.Workspace.set_show_window_fn(S.WINDOW_TITLE, self._show_window)
        self._add_menu()

        if self._settings.get(S.SETTING_AUTO_BUILD):
            try:
                self.build_stage(overwrite=False)
                self._window.refresh()
            except Exception as exc:  # noqa: BLE001
                carb.log_error(f"[{S.EXTENSION_NAME}] auto build failed: {exc}")

    def on_shutdown(self) -> None:
        global _instance
        self._remove_menu()
        ui.Workspace.set_show_window_fn(S.WINDOW_TITLE, None)
        if self._window:
            self._window.destroy()
            self._window = None
        self._stack = None
        self._sensors = None
        self._writer = None
        _instance = None

    # ----------------------------------------------------------------- menu
    def _add_menu(self) -> None:
        try:
            import omni.kit.ui
            editor_menu = omni.kit.ui.get_editor_menu()
            if editor_menu:
                self._menu = editor_menu.add_item(S.MENU_PATH, self._on_menu_click, toggle=True, value=True)
        except Exception as exc:  # noqa: BLE001 - menu is a nicety, not a requirement
            carb.log_warn(f"[{S.EXTENSION_NAME}] editor menu unavailable: {exc}")

    def _remove_menu(self) -> None:
        if self._menu:
            try:
                import omni.kit.ui
                omni.kit.ui.get_editor_menu().remove_item(self._menu)
            except Exception:  # noqa: BLE001
                pass
            self._menu = None

    def _on_menu_click(self, _menu, value: bool) -> None:
        self._show_window(value)

    def _show_window(self, value: bool) -> None:
        if self._window:
            self._window.visible = value

    def on_window_visibility_changed(self, visible: bool) -> None:
        if self._menu:
            try:
                import omni.kit.ui
                omni.kit.ui.get_editor_menu().set_value(S.MENU_PATH, visible)
            except Exception:  # noqa: BLE001
                pass

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _resolve_output_dir(value: Optional[str]) -> str:
        value = value or S.DEFAULT_LAYER_OUTPUT_DIR
        try:
            resolved = carb.tokens.get_tokens_interface().resolve(value)
        except Exception:  # noqa: BLE001
            resolved = value
        if "${" in resolved:  # token not defined in this app
            resolved = os.path.join(os.path.expanduser("~"), "Documents", S.EXTENSION_NAME, "layers")
        return os.path.abspath(resolved)

    def _require_stack(self) -> LayerStack:
        if not self._stack:
            raise RuntimeError("Build the farm stage first.")
        return self._stack

    # ------------------------------------------------------------- actions
    def build_stage(self, overwrite: bool = False) -> str:
        """
        Generate the sublayer files, then hand the root layer to omni.usd so
        the viewport, Stage window and Property panel all see the same stage.
        """
        out_dir = self._resolve_output_dir(self.layer_output_dir)
        builder = StageBuilder(out_dir, self.farm_asset_path)
        stack = builder.build(overwrite=overwrite)

        ctx = omni.usd.get_context()
        if not ctx.open_stage(stack.root_path):
            raise RuntimeError(f"omni.usd could not open {stack.root_path}")
        # Re-point the stack at the context's stage object: Sdf layers are
        # shared by identifier, so EditContexts on RUNTIME/DATA layers still
        # target the on-disk files while omni.usd owns composition.
        stack.stage = ctx.get_stage()
        StageBuilder.validate(stack)

        self._stack = stack
        self._sensors = SensorManager(stack)
        self._writer = RuntimeWriter(stack)

        if self._settings.get(S.SETTING_SPAWN_TEST_SENSORS) and not self._sensors.list_sensors():
            self._sensors.spawn_test_sensors(seed_runtime_values=True)
        self.frame_sensors()
        return f"Stage built at {out_dir} ({'fresh' if overwrite else 'kept DATA/RUNTIME'})"

    def spawn_test_sensors(self) -> str:
        prims = self._sensors_or_raise().spawn_test_sensors(seed_runtime_values=True)
        self.frame_sensors()
        return f"Spawned {len(prims)} test sensors + demo zone; seeded RUNTIME values"

    def spawn_sensor(self, sensor_id: str, position: Tuple[float, float, float], kind: str) -> str:
        if not sensor_id:
            raise ValueError("sensor id is empty")
        self._sensors_or_raise().spawn_sensor(SensorSpec(sensor_id, position, kind=kind))
        return f"Spawned {sensor_id} ({kind}) at {position}"

    def simulate_telemetry_tick(self) -> str:
        """
        UI-responsiveness check only: perturb every sensor's live values in
        RUNTIME_LYR. This is NOT the Phase 2 ingestion path (no network); it
        exercises the exact write path that ingestion will use.
        """
        stack = self._require_stack()
        rng = random.Random(int(time.time()))
        now = time.time()
        n = 0
        for prim in self._sensors.list_sensors():
            sid = prim.GetName()
            status = rng.choice(S.SENSOR_STATUSES[1:4])
            self._writer.write_sensor(sid, {
                "soilMoisture": round(rng.uniform(12, 38), 1),
                "ambientTemperature": round(rng.uniform(9, 27), 1),
                "relativeHumidity": round(rng.uniform(55, 98), 0),
                "status": status,
            }, timestamp=now)
            n += 1
        return f"Tick: updated {n} sensors in {S.RUNTIME_LAYER_FILE} (no reload)"

    def clear_runtime_layer(self) -> str:
        StageBuilder.clear_runtime_layer(self._require_stack())
        return "Runtime layer cleared; stage shows DATA + ASSET opinions only"

    def save_layers(self) -> str:
        StageBuilder.save_all(self._require_stack())
        return "All layers saved"

    def frame_sensors(self) -> Optional[str]:
        stack = self._require_stack()
        try:
            from omni.kit.viewport.utility import get_active_viewport, frame_viewport_prims
            vp = get_active_viewport()
            if vp:
                paths = [str(p.GetPath()) for p in self._sensors.list_sensors()] or [S.FARM_PATH]
                frame_viewport_prims(vp, prims=paths)
        except Exception as exc:  # noqa: BLE001 - headless / no viewport
            carb.log_info(f"[{S.EXTENSION_NAME}] frame skipped: {exc}")
        return None

    # -------------------------------------------------------------- queries
    def sensor_summary(self) -> List[Dict[str, object]]:
        return self._sensors.sensor_summary() if self._sensors else []

    def layer_stack_info(self) -> List[Dict[str, object]]:
        if not self._stack:
            return []
        roles = {
            S.RUNTIME_LAYER_FILE: "live telemetry overrides (Phase 2 write target)",
            S.SIM_LAYER_FILE: "physics / Isaac Sim (Phase 3)",
            S.DATA_LAYER_FILE: "zones + sensor definitions",
            S.ASSET_LAYER_FILE: "3D farm scan reference + placeholder ground",
        }
        rows = []
        for name in S.SUBLAYER_ORDER_STRONGEST_FIRST:
            layer = Sdf.Layer.FindOrOpen(self._stack.layer_paths[name])
            count = sum(1 for _ in _iter_prim_specs(layer)) if layer else 0
            rows.append({"name": name, "prims": count, "dirty": bool(layer and layer.dirty), "role": roles[name]})
        return rows

    def _sensors_or_raise(self) -> SensorManager:
        self._require_stack()
        return self._sensors

    @property
    def stack(self) -> Optional[LayerStack]:
        return self._stack


def _iter_prim_specs(layer: Sdf.Layer):
    stack = list(layer.rootPrims)
    while stack:
        spec = stack.pop()
        yield spec
        stack.extend(spec.nameChildren)
