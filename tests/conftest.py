"""Pytest fixtures: UTF-8 stdout so logging middleware does not fail on Windows cp1251."""
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _init_leaderboard_table():
    """TestClient may not run FastAPI lifespan before DB access; ensure table exists."""
    from leaderboard import init_leaderboard_table

    init_leaderboard_table()


def pytest_configure(config):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


@pytest.fixture
def client():
    from main import app

    return TestClient(app)
