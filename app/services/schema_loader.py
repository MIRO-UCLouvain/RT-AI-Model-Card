"""Module for loading and caching the model card schema."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import streamlit as st

_SCHEMA_PATH: Path = Path(__file__).resolve().parent.parent / "core/schemas" / "model_card_schema.json"  # noqa: E501


@st.cache_data  # This avoids reloading on every rerun
def get_model_card_schema() -> dict[str, Any]:
    """
    Load and return the model card schema.

    :return: The model card schema.
    :rtype: dict[str, Any]
    """
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return cast("dict[str, Any]", json.load(f))



