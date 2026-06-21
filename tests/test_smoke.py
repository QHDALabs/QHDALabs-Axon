"""Smoke test — potwierdza, że środowisko i import qhda-core działają."""

def test_environment():
    import numpy as np
    assert np.__version__

def test_qhda_core_available():
    """qhda-core zainstalowane (pip install -e ../qhda-core)."""
    try:
        from qhda_core import RelationalState, MeasurementOutcome
    except ImportError:
        import pytest
        pytest.skip("qhda-core nie zainstalowane — pip install -e path/to/qhda-core")
