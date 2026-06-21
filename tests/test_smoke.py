"""Smoke test — confirms the environment composes: Axon imports and its
qhda-core dependency is importable."""


def test_environment():
    import numpy as np
    assert np.__version__


def test_axon_importable():
    import axon
    assert axon.__version__


def test_qhda_core_available():
    """qhda-core is installed as a dependency (pip install -e ../qhda-core)."""
    try:
        from qhda_core import RelationalState, MeasurementOutcome  # noqa: F401
    except ImportError:
        import pytest
        pytest.skip("qhda-core not installed — pip install -e path/to/qhda-core")
