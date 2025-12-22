# SPDX-License-Identifier: Apache-2.0
"""Checkmate presets module."""

from checkmate.presets.loader import (
    PresetConfig,
    load_preset,
    preset_to_plugin_names,
    list_presets,
    get_owasp_category_for_probe,
    get_severity_for_probe,
)

__all__ = [
    "PresetConfig",
    "load_preset",
    "preset_to_plugin_names",
    "list_presets",
    "get_owasp_category_for_probe",
    "get_severity_for_probe",
]
