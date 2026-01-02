"""Tiny smoke test for Sutra package."""

def test_import():
    import sutra  # noqa: F401

    assert hasattr(sutra, "__version__")
