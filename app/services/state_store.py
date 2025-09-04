"""Module for managing Streamlit session state, and extracting information from it."""  # noqa: E501
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import streamlit as st

from app.core.date_utils import is_yyyymmdd, set_safe_date_field, to_date


def store_value(key: str) -> None:
    """
    Store the value of a key in the session state.

    :param key: The key to store the value for.
    :type key: str
    """
    st.session_state[key] = st.session_state["_" + key]

def load_value(key: str, default: object | None = None) -> None:
    """
    Load the value of a key from the session state.

    :param key: The key to load the value for.
    :type key: str
    :param default: The default value to use if the key is not found, defaults
        to None
    :type default: Optional[object], optional
    """
    if key not in st.session_state:
        st.session_state[key] = default
    st.session_state["_" + key] = st.session_state[key]

def _normalize_to_yyyymmdd(value: object) -> str | None:
    """
    Normalize different date inputs (str/datetime/date) to 'YYYYMMDD' or None.
    Accepted strings: 'YYYYMMDD', 'YYYY-MM-DD', 'YYYY/MM/DD'.

    :param value: The value to normalize.
    :type value: object
    :return: The normalized date string or None.
    :rtype: str | None
    """  # noqa: D205
    if isinstance(value, str):
        s = value.strip().replace("-", "").replace("/", "")
        return s if is_yyyymmdd(s) else None
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    return None


def populate_session_state_from_json(  # noqa: C901, PLR0912, PLR0915
    data: dict[str, Any],
) -> None:
    """
    Populate the Streamlit session state from a JSON-like dictionary.

    :param data: The data to populate the session state with.
    :type data: dict[str, Any]
    """
    if "task" in data:
        st.session_state["task"] = data["task"]

    for section, content in data.items():
        # ---------------------------
        # TRAINING DATA
        # ---------------------------
        if section == "training_data":
            for k, v in content.items():
                full_key = f"{section}_{k}"
                if not isinstance(v, list):
                    st.session_state[full_key] = v
                else:
                    st.session_state[full_key] = v
                    st.session_state[full_key + "_list"] = v

            ios: list[dict[str, Any]] = content.get(
                "inputs_outputs_technical_specifications", [],
            )
            for io in ios:
                clean: str = (
                    io["entry"]
                    .strip()
                    .replace(" ", "_")
                    .lower()
                )
                src: str = io["source"]
                for io_key, io_val in io.items():
                    if io_key not in ["entry", "source"]:
                        io_full_key = f"training_data_{clean}_{src}_{io_key}"
                        st.session_state[io_full_key] = io_val
                        raw_key = f"_{io_full_key}"
                        st.session_state[raw_key] = io_val

        # ---------------------------
        # EVALUATIONS
        # ---------------------------
        elif section == "evaluations":
            eval_names: list[str] = [entry["name"] for entry in content]
            st.session_state["evaluation_forms"] = eval_names

            for entry in content:
                name: str = entry["name"].replace(" ", "_")
                prefix: str = f"evaluation_{name}_"

                for key, value in entry.items():
                    # Inputs/outputs tech specs for this evaluation
                    if key == "inputs_outputs_technical_specifications":
                        for io in value:
                            clean2: str = (
                                io["entry"]
                                .strip()
                                .replace(" ", "_")
                                .lower()
                            )
                            src2: str = io["source"]
                            for io_key, io_val in io.items():
                                if io_key not in ["entry", "source"]:
                                    io_full_key = (
                                        prefix
                                        + clean2
                                        + "_"
                                        + src2
                                        + "_"
                                        + io_key
                                    )
                                    st.session_state[io_full_key] = io_val
                                    raw_key = f"_{io_full_key}"
                                    st.session_state[raw_key] = io_val

                    # Metric group list(s)
                    elif isinstance(value, list) and key.startswith("type_"):
                        metric_names: list[str] = [m["name"] for m in value]
                        st.session_state[f"{prefix}{key}_list"] = metric_names
                        st.session_state[f"{prefix}{key}"] = metric_names

                        for metric in value:
                            metric_prefix = (
                                f"evaluation_{name}."
                                f"{metric['name']}"
                            )
                            for m_field, m_val in metric.items():
                                if m_field != "name":
                                    st.session_state[
                                        f"{metric_prefix}_{m_field}"
                                    ] = m_val

                    elif "date" in key.lower():
                        base_key = f"{prefix}{key}"          # stores YYYYMMDD
                        widget_key = f"{base_key}_widget"
                        raw_key = f"_{widget_key}"

                        # Normalize incoming value and construct date object
                        # Seed ONCE so user edits persist across reruns
                        if (
                            base_key not in st.session_state
                            and widget_key not in st.session_state
                        ):
                            norm = _normalize_to_yyyymmdd(value)
                            if norm and is_yyyymmdd(norm):
                                d = to_date(norm)
                            else:
                                d = None
                                norm = None
                            st.session_state[base_key] = norm
                            # widget state (date or None)
                            st.session_state[widget_key] = d
                            st.session_state[raw_key] = d

                    elif isinstance(value, str) and is_yyyymmdd(value):
                        base_key = f"{prefix}{key}"
                        widget_key = f"{base_key}_widget"
                        raw_key = f"_{widget_key}"
                        if (
                            base_key not in st.session_state
                            and widget_key not in st.session_state
                        ):
                            d = to_date(value)
                            st.session_state[base_key] = value if d else None
                            st.session_state[widget_key] = d
                            st.session_state[raw_key] = d

                    # Any other simple field
                    else:
                        st.session_state[f"{prefix}{key}"] = value

        # ---------------------------
        # TECHNICAL SPECIFICATIONS
        # ---------------------------
        elif section == "technical_specifications":
            for k, v in content.items():
                if k == "learning_architectures" and isinstance(v, list):
                    st.session_state["learning_architecture_forms"] = {
                        f"Learning Architecture {i + 1}": {}
                        for i in range(len(v))
                    }
                    for i, arch in enumerate(v):
                        prefix = f"learning_architecture_{i}_"
                        for key, value in arch.items():
                            full_key = f"{prefix}{key}"
                            st.session_state[full_key] = value
                    continue

                if k == "hw_and_sw" and isinstance(v, dict):
                    for hw_sw_key, hw_sw_val in v.items():
                        full_key = f"{k}_{hw_sw_key}"
                        st.session_state[full_key] = hw_sw_val
                    continue

                full_key = f"{section}_{k}"
                st.session_state[full_key] = v

                if isinstance(v, list):
                    st.session_state[full_key + "_list"] = v

        # ---------------------------
        # GENERIC DICTIONARY SECTIONS
        # ---------------------------
        elif isinstance(content, dict):
            for k, v in content.items():
                full_key = f"{section}_{k}"

                # Handle creation_date via helper (and seed once)
                if k.endswith("creation_date"):
                    widget_key = f"{full_key}_widget"
                    raw_key = f"_{widget_key}"
                    if (
                        full_key not in st.session_state
                        and widget_key not in st.session_state
                    ):
                        norm = _normalize_to_yyyymmdd(v)
                        set_safe_date_field(full_key, norm)
                    if isinstance(v, list):
                        st.session_state[full_key + "_list"] = v
                    continue

                # Generic assignment for non-date fields
                st.session_state[full_key] = v
                if isinstance(v, list):
                    st.session_state[full_key + "_list"] = v
