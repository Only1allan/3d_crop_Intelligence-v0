"""
Register the codeless `farmSensor` schema plugin with the USD plugin registry.

Why codeless: Omniverse Kit ships its own USD build, and shipping compiled
schema libraries means matching that ABI per Kit release. A codeless schema
(`skipCodeGeneration = true` in schema.usda) is just two resource files
(generatedSchema.usda + plugInfo.json) that Usd.SchemaRegistry reads at
runtime. It gives us typed attributes, fallback values, allowedTokens and
`prim.ApplyAPI("FarmSensorAPI")` with zero native code.

Works identically in Kit and in a plain `pip install usd-core` interpreter,
which is what the headless tests rely on.
"""
from __future__ import annotations

import os
from typing import Optional

from pxr import Plug, Usd

SCHEMA_PLUGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "farmSensor")
_PLUGIN_NAME = "farmSensor"
_REGISTERED = False


def is_schema_registered() -> bool:
    """True once Usd.SchemaRegistry knows FarmSensorAPI."""
    try:
        return bool(Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("FarmSensorAPI"))
    except Exception:  # pragma: no cover - very old USD
        return False


def register_schema_plugin(plugin_dir: Optional[str] = None) -> bool:
    """
    Idempotently register the plugin directory. Returns True when the schema
    is usable afterwards. Safe to call on every extension startup: Plug will
    not double-register the same path.
    """
    global _REGISTERED
    plugin_dir = plugin_dir or SCHEMA_PLUGIN_DIR
    if _REGISTERED and is_schema_registered():
        return True

    plug_info = os.path.join(plugin_dir, "plugInfo.json")
    if not os.path.isfile(plug_info):
        raise FileNotFoundError(
            f"Schema plugin not found at {plug_info}. Run `python tools/gen_schema.py` to regenerate."
        )

    plugins = Plug.Registry().RegisterPlugins(plugin_dir)
    names = [p.name for p in plugins]
    # RegisterPlugins returns [] if the path was already registered earlier in
    # this process, so fall through to the schema-registry check either way.
    _REGISTERED = is_schema_registered()
    if not _REGISTERED:
        raise RuntimeError(
            f"Registered plugins {names} from {plugin_dir} but FarmSensorAPI is still unknown. "
            "Check plugInfo.json 'Root'/'ResourcePath' are '.' and generatedSchema.usda exists."
        )
    return True
