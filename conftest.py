"""
pytest configuration and shared fixtures for all test modules.
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(autouse=True)
def reset_user_env():
    """Reset CURRENT_USER_ID between tests to prevent state leakage."""
    original = os.environ.get("CURRENT_USER_ID")
    yield
    if original is not None:
        os.environ["CURRENT_USER_ID"] = original
    elif "CURRENT_USER_ID" in os.environ:
        del os.environ["CURRENT_USER_ID"]


@pytest.fixture
def as_alice():
    os.environ["CURRENT_USER_ID"] = "alice"


@pytest.fixture
def as_bob():
    os.environ["CURRENT_USER_ID"] = "bob"


@pytest.fixture
def as_admin():
    os.environ["CURRENT_USER_ID"] = "admin"
