"""Tests for the elite local interface."""

from __future__ import annotations

import pytest

from fps_booster.interface import EliteConfiguration, EliteInterface


def test_interface_exposes_over_fifty_controls() -> None:
    interface = EliteInterface()
    configs = interface.list_configurations()
    assert len(configs) >= 50
    assert configs["target_fps"] == 165


def test_interface_reports_abundant_methods() -> None:
    interface = EliteInterface()
    methods = interface.available_methods()
    assert "render_dashboard" in methods
    assert len(methods) >= 25


def test_apply_and_register_presets() -> None:
    interface = EliteInterface()
    preset = EliteConfiguration(target_fps=200, latency_budget_ms=10.0)
    interface.register_preset("tournament", preset)
    applied = interface.apply_preset("tournament")
    assert applied.target_fps == 200
    assert interface.list_configurations()["latency_budget_ms"] == 10.0


def test_macros_update_configuration() -> None:
    interface = EliteInterface()
    invoked: dict[str, bool] = {}

    def macro(iface: EliteInterface) -> None:
        invoked["flag"] = True
        iface.set_option("target_fps", 188)

    interface.register_macro("velvet-surge", macro)
    interface.invoke_macro("velvet-surge")
    assert invoked["flag"] is True
    assert interface.list_configurations()["target_fps"] == 188
    assert interface.macro_count() == 1


def test_validation_rejects_incoherent_values() -> None:
    interface = EliteInterface()
    interface.set_option("minimum_fps", 200)
    interface.set_option("target_fps", 190)
    with pytest.raises(ValueError):
        interface.validate_integrity()


def test_theme_roundtrip() -> None:
    interface = EliteInterface()
    profile = interface.export_profile()
    profile["config"]["target_fps"] = 150
    profile["theme"]["name"] = "Royal Impact"
    interface.import_profile(profile)
    interface.validate_integrity()
    dashboard = interface.render_dashboard()
    assert "Royal Impact" in interface.describe_theme()
    assert "Royal Impact" in dashboard


def test_roi_projection_and_multiplier() -> None:
    interface = EliteInterface()
    baseline = interface.project_roi()
    adjusted = interface.apply_investment_multiplier(9.2)
    assert adjusted > baseline

