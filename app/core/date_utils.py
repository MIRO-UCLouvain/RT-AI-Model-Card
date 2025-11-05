"""Module for date validation and conversion utilities."""
from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TypeGuard

import streamlit as st

# Named constant for the expected length of a YYYYMMDD date string.
DATE_STR_LEN = 8

def is_yyyymmdd(s: object) -> TypeGuard[str]:
    """
    Check if a value is a string in YYYYMMDD format.

    :param s: Value to test.
    :type s: object
    :return: True if `s` is a string of 8 digits, otherwise False.
    :rtype: bool
    """
    return isinstance(s, str) and len(s) == DATE_STR_LEN and s.isdigit()


def to_date(s: str) -> date | None:
    """
    Convert a YYYYMMDD string to a :class:`datetime.date`.

    :param s: A string in YYYYMMDD format.
    :type s: str
    :return: The parsed :class:`datetime.date` if valid, otherwise None.
    :rtype: date | None
    """
    try:
        # make the datetime timezone-aware (UTC) to avoid
        # naive-datetime construction,
        # then extract the date portion
        tzinfo = UTC
        return datetime.strptime(s, "%Y%m%d").replace(tzinfo=tzinfo).date()
    except (ValueError, TypeError):
        return None


def set_safe_date_field(base_key: str, yyyymmdd_string: str | None) -> None:
    """
    Set a safe date field in the Streamlit session state.

    :param base_key: The base key for the date field.
    :type base_key: str
    :param yyyymmdd_string: The date string in YYYYMMDD format.
    :type yyyymmdd_string: str | None
    """
    widget_key = f"{base_key}_widget"
    raw_key = f"_{widget_key}"

    parsed_date: date | None
    if is_yyyymmdd(yyyymmdd_string):
        # mypy: yyyymmdd_string is str here
        parsed_date = to_date(yyyymmdd_string)
    else:
        parsed_date = None

    st.session_state[base_key] = yyyymmdd_string if parsed_date else None
    st.session_state[widget_key] = parsed_date
    st.session_state[raw_key] = parsed_date
