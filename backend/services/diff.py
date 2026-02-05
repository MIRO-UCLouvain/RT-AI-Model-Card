"""Deep JSON diff for model card content comparison.

Compares two model card content dicts (as produced by the frontend serialiser)
and returns a structured result keyed by section name.

Algorithm
---------
1. Walk every top-level key that appears in either old or new.
2. If a key maps to a dict on both sides  → field-level diff inside that section.
3. If a key maps to a list on both sides  → element-level diff (match by index;
   missing trailing items are added/removed, changed items carry old+new).
4. Primitive values (str, int, bool, None)  → simple equality check.
5. Type mismatches (dict vs list, etc.)     → treated as "changed".

Empty strings and None are normalised to None before comparison so that
clearing a text field is not confused with never having filled it.

Output shape
------------
{
  "<section>": {
    "added":   [{"field": str, "value": <any>}, ...],
    "removed": [{"field": str, "value": <any>}, ...],
    "changed": [{"field": str, "old": <any>, "new": <any>}, ...]
  },
  ...
}

Only sections that actually differ are included in the output dict.
"""

from __future__ import annotations

from typing import Any

# Sentinel that is definitely not equal to any JSON value (including None).
_MISSING: Any = object()


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise(value: Any) -> Any:
    """Treat empty string as None for comparison purposes."""
    if value is None or value == "":
        return None
    return value


def _values_equal(a: Any, b: Any) -> bool:
    """Return True if a and b are semantically equal after normalisation."""
    # Recursively normalise dicts and lists so that {"x": ""} == {"x": None}.
    a = _deep_normalise(a)
    b = _deep_normalise(b)
    return a == b


def _deep_normalise(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_normalise(v) for v in value]
    return _normalise(value)


# ---------------------------------------------------------------------------
# Core diff primitives
# ---------------------------------------------------------------------------

def _diff_flat_section(
    old: dict[str, Any],
    new: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Diff two flat-ish section dicts.

    Values that are themselves dicts or lists are compared as opaque blobs
    (deep equality).  Callers that need finer-grained list diffs should
    post-process the "changed" entries themselves.
    """
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []

    all_keys = sorted(set(old.keys()) | set(new.keys()))
    for key in all_keys:
        old_raw = old.get(key, _MISSING)
        new_raw = new.get(key, _MISSING)

        if old_raw is _MISSING:
            added.append({"field": key, "value": new_raw})
        elif new_raw is _MISSING:
            removed.append({"field": key, "value": old_raw})
        elif not _values_equal(old_raw, new_raw):
            changed.append({"field": key, "old": old_raw, "new": new_raw})

    return {"added": added, "removed": removed, "changed": changed}


def _diff_list(
    old_list: list[Any],
    new_list: list[Any],
    field: str,
) -> dict[str, list[dict[str, Any]]]:
    """Diff two lists at the element level (aligned by index).

    Returns the same {added, removed, changed} shape as _diff_flat_section,
    but each entry carries an "index" key instead of "field".
    """
    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []

    max_len = max(len(old_list), len(new_list))
    for i in range(max_len):
        if i >= len(old_list):
            added.append({"field": f"{field}[{i}]", "value": new_list[i]})
        elif i >= len(new_list):
            removed.append({"field": f"{field}[{i}]", "value": old_list[i]})
        elif not _values_equal(old_list[i], new_list[i]):
            changed.append({"field": f"{field}[{i}]", "old": old_list[i], "new": new_list[i]})

    return {"added": added, "removed": removed, "changed": changed}


def _merge_diffs(
    *diffs: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Merge multiple {added, removed, changed} dicts into one."""
    merged: dict[str, list[dict[str, Any]]] = {
        "added": [],
        "removed": [],
        "changed": [],
    }
    for d in diffs:
        merged["added"].extend(d.get("added", []))
        merged["removed"].extend(d.get("removed", []))
        merged["changed"].extend(d.get("changed", []))
    return merged


def _diff_section_value(
    key: str,
    old_val: Any,
    new_val: Any,
) -> dict[str, list[dict[str, Any]]]:
    """Produce the section-level diff for one top-level key."""
    if isinstance(old_val, dict) and isinstance(new_val, dict):
        # Separate list-valued fields from flat fields for richer output.
        flat_old: dict[str, Any] = {}
        flat_new: dict[str, Any] = {}
        list_keys: set[str] = set()

        all_inner = sorted(set(old_val.keys()) | set(new_val.keys()))
        for ik in all_inner:
            ov = old_val.get(ik, _MISSING)
            nv = new_val.get(ik, _MISSING)
            # If either side is a list, use list-level diff.
            if (ov is not _MISSING and isinstance(ov, list)) or (
                nv is not _MISSING and isinstance(nv, list)
            ):
                list_keys.add(ik)
            else:
                if ov is not _MISSING:
                    flat_old[ik] = ov
                if nv is not _MISSING:
                    flat_new[ik] = nv

        parts: list[dict[str, list[dict[str, Any]]]] = [
            _diff_flat_section(flat_old, flat_new)
        ]

        for lk in sorted(list_keys):
            ov = old_val.get(lk, _MISSING)
            nv = new_val.get(lk, _MISSING)
            old_list = ov if ov is not _MISSING and isinstance(ov, list) else []
            new_list = nv if nv is not _MISSING and isinstance(nv, list) else []

            if _values_equal(old_list, new_list):
                continue

            if ov is _MISSING:
                parts.append({
                    "added": [{"field": lk, "value": nv}],
                    "removed": [],
                    "changed": [],
                })
            elif nv is _MISSING:
                parts.append({
                    "added": [],
                    "removed": [{"field": lk, "value": ov}],
                    "changed": [],
                })
            else:
                parts.append(_diff_list(old_list, new_list, lk))

        return _merge_diffs(*parts)

    if isinstance(old_val, list) and isinstance(new_val, list):
        if _values_equal(old_val, new_val):
            return {"added": [], "removed": [], "changed": []}
        return _diff_list(old_val, new_val, key)

    # Primitive or type mismatch
    if _values_equal(old_val, new_val):
        return {"added": [], "removed": [], "changed": []}
    return {
        "added": [],
        "removed": [],
        "changed": [{"field": key, "old": old_val, "new": new_val}],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_diff(
    old_content: dict[str, Any],
    new_content: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Compute a deep structural diff between two model card content dicts.

    Parameters
    ----------
    old_content:
        The earlier version's content JSON.
    new_content:
        The later version's content JSON.

    Returns
    -------
    A dict keyed by section name.  Only sections that actually differ are
    included.  Each value has the shape::

        {
          "added":   [{"field": str, "value": <any>}],
          "removed": [{"field": str, "value": <any>}],
          "changed": [{"field": str, "old": <any>, "new": <any>}],
        }
    """
    result: dict[str, dict[str, list[dict[str, Any]]]] = {}

    all_keys = sorted(set(old_content.keys()) | set(new_content.keys()))

    for key in all_keys:
        old_raw = old_content.get(key, _MISSING)
        new_raw = new_content.get(key, _MISSING)

        if old_raw is _MISSING:
            # Entire section is new
            result[key] = {
                "added": [{"field": key, "value": new_raw}],
                "removed": [],
                "changed": [],
            }
            continue

        if new_raw is _MISSING:
            # Entire section was removed
            result[key] = {
                "added": [],
                "removed": [{"field": key, "value": old_raw}],
                "changed": [],
            }
            continue

        section_diff = _diff_section_value(key, old_raw, new_raw)

        # Only include sections that have at least one change.
        if any(section_diff[k] for k in ("added", "removed", "changed")):
            result[key] = section_diff

    return result
