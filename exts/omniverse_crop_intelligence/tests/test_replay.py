"""
Headless tests for time-sampled replay writes (RuntimeWriter.write_*_series).

Invariants introduced with the series writers:
  * series land in RUNTIME_LYR as time samples ONLY (no default opinion --
    the composed stage keeps schema fallbacks until scrubbed),
  * the allow-list firewall applies (identity attrs stay DATA-layer),
  * samples persist with the layer and vanish on clear_runtime_layer.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.dirname(HERE)
if EXT_ROOT not in sys.path:
    sys.path.insert(0, EXT_ROOT)

pxr = pytest.importorskip("pxr")
from pxr import Sdf, Usd  # noqa: E402

from omniverse_crop_intelligence import settings as S  # noqa: E402
from omniverse_crop_intelligence.schema import FarmZoneAPI  # noqa: E402
from omniverse_crop_intelligence.sensor_manager import SensorManager, ZoneSpec  # noqa: E402
from omniverse_crop_intelligence.phase2.runtime_writer import RuntimeWriter  # noqa: E402
from omniverse_crop_intelligence.stage_builder import StageBuilder  # noqa: E402


@pytest.fixture()
def stack(tmp_path):
    builder = StageBuilder(str(tmp_path / "layers"))
    return builder.build(overwrite=True)


@pytest.fixture()
def demo(stack):
    mgr = SensorManager(stack)
    mgr.spawn_test_sensors(seed_runtime_values=True)
    return mgr, RuntimeWriter(stack)


def test_zone_series_author_time_samples_only(demo, stack):
    mgr, w = demo
    # A zone with NO seeded values proves the series writer authors time
    # samples only -- never a default opinion.
    mgr.spawn_zone(ZoneSpec(zone_id="Zone_Replay", display_name="Replay only",
                            position=(5.0, 5.0, 0.0), source="farmwise_plot"))
    zone = stack.stage.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_Replay")
    api = FarmZoneAPI(zone)
    n_prims = len(list(stack.stage.Traverse()))

    n = w.write_zone_series("Zone_Replay", {
        "ndvi": [(38, 0.55), (45, 0.61), (60, 0.74)],
        "daysAfterPlanting": [(float(d), float(d)) for d in range(38, 68)],
    })
    assert n == 33
    assert len(list(stack.stage.Traverse())) == n_prims, "series writes must not add prims"

    ndvi = api.attr("ndvi")
    assert ndvi.GetTimeSamples() == [38.0, 45.0, 60.0]
    assert ndvi.Get(Usd.TimeCode(45)) == pytest.approx(0.61)
    assert ndvi.Get(Usd.TimeCode.Default()) == pytest.approx(0.0), \
        "no default opinion: fallback holds until scrubbed"

    # The samples live in RUNTIME_LYR; DATA_LYR never gets a spec for them.
    rt_spec = stack.runtime_layer.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_Replay")
    assert rt_spec.attributes["farmZone:ndvi"].ListTimeSamples() == [38.0, 45.0, 60.0]
    data_spec = stack.data_layer.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_Replay")
    assert "farmZone:ndvi" not in data_spec.attributes, "series must not land in DATA_LYR"


def test_sensor_series_and_unknown_targets(demo):
    mgr, w = demo
    n = w.write_sensor_series("WeatherStation_C", {
        "ambientTemperature": [(40, 15.2), (41, 16.8)],
        "precipitation": [(40, 0.0), (41, 3.5)],  # authored zero: a dry day
    })
    assert n == 4
    api = mgr.get_sensor("WeatherStation_C")
    assert api.attr("ambientTemperature").Get(Usd.TimeCode(41)) == pytest.approx(16.8)
    assert api.attr("precipitation").Get(Usd.TimeCode(40)) == pytest.approx(0.0)

    with pytest.raises(ValueError):
        w.write_sensor_series("WeatherStation_C", {"sensorId": [(1, 2)]})
    with pytest.raises(KeyError):
        w.write_sensor_series("Nope", {"ndvi": [(1, 2)]})
    with pytest.raises(ValueError):
        w.write_zone_series("Zone_DemoPlot", {"variety": [(1, 2)]})
    with pytest.raises(KeyError):
        w.write_zone_series("Nope", {"ndvi": [(1, 2)]})


def test_series_persist_then_clear(demo, stack, tmp_path):
    mgr, w = demo
    w.write_zone_series("Zone_DemoPlot", {"ndvi": [(38, 0.55), (67, 0.78)]}, save=True)
    w.write_sensor_series("WeatherStation_C", {"ambientTemperature": [(50, 21.4)]}, save=True)
    StageBuilder.save_all(stack)

    reopened = StageBuilder(stack.output_dir).build(overwrite=False)
    zone_api = FarmZoneAPI(reopened.stage.GetPrimAtPath(f"{S.ZONES_PATH}/Zone_DemoPlot"))
    assert zone_api.attr("ndvi").Get(Usd.TimeCode(67)) == pytest.approx(0.78)
    sensor_api = SensorManager(reopened).get_sensor("WeatherStation_C")
    assert sensor_api.attr("ambientTemperature").Get(Usd.TimeCode(50)) == pytest.approx(21.4)

    StageBuilder.clear_runtime_layer(reopened)
    assert zone_api.attr("ndvi").GetTimeSamples() == []
    assert zone_api.attr("ndvi").Get(Usd.TimeCode(67)) == pytest.approx(0.0)
