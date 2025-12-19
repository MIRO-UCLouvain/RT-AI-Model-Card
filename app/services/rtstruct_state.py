"""Shared RTSTRUCT groups state management.

RTSTRUCT groups are a global concept: each group has a short display name
("RTSTRUCT 1", "RTSTRUCT 2", …) and a list of anatomical structures.

They are defined once and can be referenced (included/excluded) independently
in model_inputs and model_outputs.  Training and evaluation technical
characteristics automatically show the organs defined here.
"""

from __future__ import annotations

import uuid as _uuid

import streamlit as st

RTSTRUCT_GROUPS_KEY = "rtstruct_groups"


def init_rtstruct_groups() -> None:
    """Ensure the global RTSTRUCT groups dict exists in session state."""
    if RTSTRUCT_GROUPS_KEY not in st.session_state:
        st.session_state[RTSTRUCT_GROUPS_KEY] = {}


def get_rtstruct_groups() -> dict[str, dict]:
    """Return the global RTSTRUCT groups dict ``{uid: {name, organs}}``."""
    return st.session_state.get(RTSTRUCT_GROUPS_KEY, {})


def get_organs_for_group_name(name: str) -> list[str]:
    """Return the organs list for the group with the given display name."""
    for g in get_rtstruct_groups().values():
        if g["name"] == name:
            return list(g.get("organs", []))
    return []


def add_rtstruct_group() -> tuple[str, str]:
    """Create a new RTSTRUCT group and return ``(uid, display_name)``."""
    init_rtstruct_groups()
    groups: dict = st.session_state[RTSTRUCT_GROUPS_KEY]
    n = len(groups) + 1
    uid = _uuid.uuid4().hex[:8]
    name = f"RTSTRUCT {n}"
    groups[uid] = {"name": name, "organs": []}
    return uid, name


def delete_rtstruct_group(uid: str) -> None:
    """Delete a RTSTRUCT group.

    After deletion the remaining groups are renumbered consecutively.
    All list-type session-state keys are updated to remove the deleted
    group's name and reflect any renames.
    """
    groups: dict = st.session_state.get(RTSTRUCT_GROUPS_KEY, {})
    if uid not in groups:
        return

    old_name: str = groups[uid]["name"]
    del groups[uid]

    # Build rename map for the remaining groups (keep them consecutive).
    rename_map: dict[str, str] = {}
    for i, (_gid, gdata) in enumerate(groups.items()):
        new_name = f"RTSTRUCT {i + 1}"
        if gdata["name"] != new_name:
            rename_map[gdata["name"]] = new_name
            gdata["name"] = new_name

    # Propagate removals and renames to all list-type session-state keys.
    for key, val in list(st.session_state.items()):
        if not isinstance(key, str) or key.startswith("_") or not isinstance(val, list):
            continue
        updated = [rename_map.get(item, item) for item in val if item != old_name]
        if updated != val:
            st.session_state[key] = updated
