"""
Tests for app.core.date_utils.

Validate parsing and session-state effects using a streamlit stub.
"""

import importlib
import sys
from collections.abc import MutableMapping
from datetime import date
from types import ModuleType
from typing import Any, cast

import pytest


class _StreamlitStub(ModuleType):
    """Typed stub so mypy knows session_state exists."""
    session_state: MutableMapping[str, Any]


def _du() -> ModuleType:
    """Import (or reload) app.core.date_utils after the stub is in place."""
    name = "app.core.date_utils"
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


@pytest.fixture(autouse=True)
def mock_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a minimal streamlit stub with a session_state mapping."""
    fake = _StreamlitStub("streamlit")
    fake.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", fake)


def test_is_yyyymmdd_happy_path() -> None:
    """Accepts an 8-digit string."""
    du = _du()
    assert du.is_yyyymmdd("20250131") is True


@pytest.mark.parametrize(
    "val", [None, 12345678, "2025-0131", "2025013", "abc"],
)
def test_is_yyyymmdd_rejects_non_8_digit_strings(val: object) -> None:
    """Rejects non-strings and non-8-digit values."""
    du = _du()
    assert du.is_yyyymmdd(val) is False


def test_to_date_valid_roundtrip() -> None:
    """Parses a valid date string."""
    du = _du()
    assert du.to_date("20250228") == date(2025, 2, 28)


@pytest.mark.parametrize(
    "s", ["20250230", "20250010", "20251301", "abcdef12", "", "2025"],
)
def test_to_date_invalid_returns_none(s: str) -> None:
    """Invalid or malformed strings return None."""
    du = _du()
    assert du.to_date(s) is None


def test_to_date_handles_typeerror_gracefully() -> None:
    """None input is handled and returns None."""
    du = _du()
    assert du.to_date(None) is None


def test_set_safe_date_field_with_valid_date_sets_all_fields() -> None:
    """Valid date updates all related session_state keys."""
    du = _du()
    st = sys.modules["streamlit"]
    ss = cast("MutableMapping[str, Any]", st.session_state)

    du.set_safe_date_field("start_date", "20240115")

    assert ss["start_date"] == "20240115"
    assert ss["start_date_widget"] == date(2024, 1, 15)
    assert ss["_start_date_widget"] == date(2024, 1, 15)


def test_set_safe_date_field_with_invalid_date_sets_nones() -> None:
    """Invalid date sets the base and widget keys to None."""
    du = _du()
    st = sys.modules["streamlit"]
    ss = cast("MutableMapping[str, Any]", st.session_state)

    du.set_safe_date_field("end_date", "20240230")

    assert ss["end_date"] is None
    assert ss["end_date_widget"] is None
    assert ss["_end_date_widget"] is None
