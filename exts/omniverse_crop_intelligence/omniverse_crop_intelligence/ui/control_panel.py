"""
omni.ui control panel for the farm digital twin.

The window is deliberately "dumb": every button calls back into the
extension controller (extension.py) which owns the stage, the layer stack and
the sensor manager. That keeps omni.ui out of the testable core.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import omni.ui as ui

from .. import settings as S

if TYPE_CHECKING:  # pragma: no cover
    from ..extension import OmniverseCropIntelligenceExtension

_LABEL_W = 110
_ROW_H = 24


class ControlPanelWindow:
    def __init__(self, controller: "OmniverseCropIntelligenceExtension"):
        self._c = controller
        self._asset_model = ui.SimpleStringModel(controller.farm_asset_path)
        self._outdir_model = ui.SimpleStringModel(controller.layer_output_dir)
        self._new_id_model = ui.SimpleStringModel("Sensor_New")
        self._x_model = ui.SimpleFloatModel(0.0)
        self._y_model = ui.SimpleFloatModel(0.0)
        self._z_model = ui.SimpleFloatModel(0.0)
        self._kind_model = None
        self._status_label = None
        self._layer_stack_frame = None
        self._sensor_list_frame = None

        self._window = ui.Window(
            S.WINDOW_TITLE, width=440, height=680,
            dockPreference=ui.DockPreference.RIGHT_BOTTOM,
        )
        self._window.set_visibility_changed_fn(self._on_visibility_changed)
        self._build()

    # ------------------------------------------------------------------ public
    @property
    def visible(self) -> bool:
        return bool(self._window and self._window.visible)

    @visible.setter
    def visible(self, value: bool) -> None:
        if self._window:
            self._window.visible = value

    def destroy(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None

    def set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.text = text

    def refresh(self) -> None:
        self._rebuild_layer_stack()
        self._rebuild_sensor_list()

    # ------------------------------------------------------------------- build
    def _build(self) -> None:
        with self._window.frame:
            with ui.ScrollingFrame(horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF):
                with ui.VStack(spacing=8, height=0):
                    ui.Label("Farm Digital Twin  -  Phase 1 foundation", style={"font_size": 18}, height=28)

                    with ui.CollapsableFrame("Stage", collapsed=False):
                        with ui.VStack(spacing=4, height=0):
                            self._row("Farm asset", ui.StringField, model=self._asset_model)
                            self._row("Layer folder", ui.StringField, model=self._outdir_model)
                            with ui.HStack(height=28, spacing=4):
                                ui.Button("Build Farm Stage", clicked_fn=lambda: self._guard(self._on_build, False))
                                ui.Button("Rebuild (wipe DATA + RUNTIME)", clicked_fn=lambda: self._guard(self._on_build, True))
                            with ui.HStack(height=28, spacing=4):
                                ui.Button("Save Layers", clicked_fn=lambda: self._guard(self._c.save_layers))
                                ui.Button("Frame Sensors", clicked_fn=lambda: self._guard(self._c.frame_sensors))

                    with ui.CollapsableFrame("Layer stack (strongest first)", collapsed=False):
                        self._layer_stack_frame = ui.VStack(spacing=2, height=0)

                    with ui.CollapsableFrame("Sensors", collapsed=False):
                        with ui.VStack(spacing=4, height=0):
                            with ui.HStack(height=28, spacing=4):
                                ui.Button("Spawn 3 Test Sensors", clicked_fn=lambda: self._guard(self._c.spawn_test_sensors))
                                ui.Button("Simulate Telemetry Tick", clicked_fn=lambda: self._guard(self._c.simulate_telemetry_tick))
                            ui.Separator(height=6)
                            ui.Label("Spawn custom sensor", height=_ROW_H)
                            self._row("Sensor id", ui.StringField, model=self._new_id_model)
                            with ui.HStack(height=_ROW_H, spacing=4):
                                ui.Label("Position (m)", width=_LABEL_W)
                                ui.FloatField(model=self._x_model)
                                ui.FloatField(model=self._y_model)
                                ui.FloatField(model=self._z_model)
                            with ui.HStack(height=_ROW_H, spacing=4):
                                ui.Label("Kind", width=_LABEL_W)
                                combo = ui.ComboBox(0, *S.SENSOR_KINDS)
                                self._kind_model = combo.model
                            ui.Button("Spawn Sensor", height=28, clicked_fn=lambda: self._guard(self._on_spawn_custom))
                            ui.Separator(height=6)
                            self._sensor_list_frame = ui.VStack(spacing=2, height=0)

                    with ui.CollapsableFrame("Runtime layer", collapsed=False):
                        with ui.VStack(spacing=4, height=0):
                            ui.Label("Live values compose as overrides in RUNTIME_LYR.usda; "
                                     "clearing never touches definitions or geometry.",
                                     word_wrap=True, height=0)
                            ui.Button("Clear Runtime Layer", height=28,
                                      clicked_fn=lambda: self._guard(self._c.clear_runtime_layer))

                    self._status_label = ui.Label("Idle", word_wrap=True, height=0,
                                                  style={"color": 0xFFB0B0B0})
        self.refresh()

    @staticmethod
    def _row(label: str, widget_cls, **kwargs):
        with ui.HStack(height=_ROW_H, spacing=4):
            ui.Label(label, width=_LABEL_W)
            return widget_cls(**kwargs)

    def _guard(self, fn, *args) -> None:
        """Run a controller action, surface exceptions in the status line, refresh."""
        try:
            result = fn(*args)
            if isinstance(result, str):
                self.set_status(result)
        except Exception as exc:  # noqa: BLE001 - UI must never crash Kit
            import traceback
            traceback.print_exc()
            self.set_status(f"ERROR: {exc}")
        finally:
            self.refresh()

    # ---------------------------------------------------------------- actions
    def _on_build(self, overwrite: bool) -> str:
        self._c.farm_asset_path = self._asset_model.as_string.strip() or S.DEFAULT_FARM_ASSET_PATH
        self._c.layer_output_dir = self._outdir_model.as_string.strip()
        return self._c.build_stage(overwrite=overwrite)

    def _on_spawn_custom(self) -> str:
        kind = S.SENSOR_KINDS[self._kind_model.get_item_value_model().as_int]
        return self._c.spawn_sensor(
            self._new_id_model.as_string.strip(),
            (self._x_model.as_float, self._y_model.as_float, self._z_model.as_float),
            kind,
        )

    def _on_visibility_changed(self, visible: bool) -> None:
        self._c.on_window_visibility_changed(visible)

    # ---------------------------------------------------------------- refresh
    def _rebuild_layer_stack(self) -> None:
        if not self._layer_stack_frame:
            return
        self._layer_stack_frame.clear()
        info = self._c.layer_stack_info()
        with self._layer_stack_frame:
            if not info:
                ui.Label("No stage built yet.", height=_ROW_H)
                return
            for row in info:
                with ui.HStack(height=_ROW_H, spacing=6):
                    ui.Label(row["name"], width=130)
                    ui.Label(f"{row['prims']} prims", width=70)
                    ui.Label("dirty" if row["dirty"] else "saved", width=50,
                             style={"color": 0xFF40A0FF if row["dirty"] else 0xFF80C080})
                    ui.Label(row["role"], word_wrap=True)

    def _rebuild_sensor_list(self) -> None:
        if not self._sensor_list_frame:
            return
        self._sensor_list_frame.clear()
        rows = self._c.sensor_summary()
        with self._sensor_list_frame:
            if not rows:
                ui.Label("No sensors in /World/Sensors.", height=_ROW_H)
                return
            with ui.HStack(height=_ROW_H):
                for h, w in (("id", 130), ("kind", 110), ("status", 60), ("moist %", 55), ("T C", 45), ("RH %", 45)):
                    ui.Label(h, width=w, style={"color": 0xFF9A9A9A})
            for r in rows:
                with ui.HStack(height=_ROW_H):
                    ui.Label(str(r["id"]), width=130)
                    ui.Label(str(r["kind"]), width=110)
                    colour = {"nominal": 0xFF40C060, "warning": 0xFF30C0F0, "critical": 0xFF3030E0}.get(r["status"], 0xFFA0A0A0)
                    ui.Label(str(r["status"]), width=60, style={"color": colour})
                    ui.Label(f"{r['soilMoisture']:.1f}", width=55)
                    ui.Label(f"{r['ambientTemperature']:.1f}", width=45)
                    ui.Label(f"{r['relativeHumidity']:.0f}", width=45)
