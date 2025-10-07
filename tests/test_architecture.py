from fps_booster.architecture import build_default_architecture, describe_architecture


def test_default_architecture_structure():
    modules = build_default_architecture()
    assert {m.name for m in modules} == {
        "Vision Analyzer",
        "Audio Intelligence",
        "Adaptive Performance",
        "Cognitive Coach",
        "Narrative Overlay",
    }
    for module in modules:
        assert module.inputs
        assert module.outputs
        assert isinstance(module.summary(), str)


def test_describe_architecture_output():
    modules = build_default_architecture()
    overview = describe_architecture(modules)
    assert overview.startswith("Arena Helper Architecture:")
    assert "Vision Analyzer" in overview
    assert "Narrative Overlay" in overview
    lines = overview.splitlines()
    assert len(lines) == 1 + 3 * len(modules)
