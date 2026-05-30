"""
Shared pytest fixtures for the Smart Retail Assistant test suite.

All tests import from here via pytest's automatic conftest discovery.
The FastAPI TestClient fixture patches the database at the module level
so main.py can be imported without a live PostgreSQL connection.
"""

import sys
import os
import types
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Make sure the backend root is on sys.path so imports like
# `from services.blob_service import ...` resolve correctly when pytest
# is run from the backend/ directory.
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# ---------------------------------------------------------------------------
# Stub out heavy / side-effectful modules BEFORE main.py is imported.
# This prevents real DB connections, model loads, and Azure SDK calls
# during test collection.
# ---------------------------------------------------------------------------

def _stub_database():
    """
    Replace the `database` module with a lightweight stub so that
    `from database import engine, Base, SessionLocal` in main.py
    doesn't attempt a real PostgreSQL connection.
    """
    stub = types.ModuleType("database")
    stub.engine = MagicMock()
    stub.Base = MagicMock()
    stub.SessionLocal = MagicMock()
    sys.modules["database"] = stub


def _stub_db_models():
    """Stub db_models so SQLAlchemy ORM classes don't need a real engine."""
    stub = types.ModuleType("db_models")
    stub.ForecastRecord = MagicMock()
    stub.ChatHistory = MagicMock()
    sys.modules["db_models"] = stub


def _stub_db_service():
    """Stub db_service so save_chat / save_forecast are no-ops."""
    stub = types.ModuleType("services.db_service")
    stub.save_forecast = MagicMock(return_value=None)
    stub.save_chat = MagicMock(return_value=None)
    sys.modules["services.db_service"] = stub


# Apply stubs once at import time (before any test module imports main)
_stub_database()
_stub_db_models()
_stub_db_service()


# ---------------------------------------------------------------------------
# Shared forecast DataFrame factory
# ---------------------------------------------------------------------------

def make_forecast_df(periods: int = 7):
    """Return a minimal Prophet-style forecast DataFrame."""
    import pandas as pd
    dates = pd.date_range(start="2026-06-01", periods=periods, freq="W")
    return pd.DataFrame({
        "ds": dates,
        "yhat":       [100_000.0 + i * 1_000 for i in range(periods)],
        "yhat_lower": [90_000.0]  * periods,
        "yhat_upper": [110_000.0] * periods,
    })


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """
    Session-scoped FastAPI TestClient.

    Imports main.py only once per test session (after stubs are in place)
    and returns a reusable TestClient instance.
    """
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
