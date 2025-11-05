"""
Unit tests for app.core.collections: helpers to splice into OrderedDicts.
Uses package imports to avoid any path issues or stdlib name clashes.
"""  # noqa: D205

import importlib
import sys
from collections import OrderedDict
from types import ModuleType


def _coll() -> ModuleType:
    """Import (or reload) app.core.collections for each test."""
    name = "app.core.collections"
    if name in sys.modules:
        return importlib.reload(sys.modules[name])
    return importlib.import_module(name)


def test_insert_after_on_empty_creates_singleton() -> None:
    """Test that inserting into an empty OrderedDict creates a singleton."""
    m = _coll()
    out = m.insert_after({}, "k", 1, "anything")
    assert isinstance(out, OrderedDict)
    assert list(out.items()) == [("k", 1)]


def test_insert_after_inserts_after_existing_key() -> None:
    """Test that inserting after an existing key works correctly."""
    m = _coll()
    base = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
    out = m.insert_after(base, "x", 99, "b")
    assert list(out.items()) == [
        ("a", 1),
        ("b", 2),
        ("x", 99),
        ("c", 3),
    ]


def test_insert_after_no_match_keeps_original() -> None:
    """Test that inserting after a non-existent key keeps the original dict unchanged."""  # noqa: E501
    m = _coll()
    base = OrderedDict([("a", 1), ("b", 2)])
    out = m.insert_after(base, "x", 99, "zzz")
    assert list(out.items()) == [("a", 1), ("b", 2)]


def test_insert_dict_after_merges_all_pairs_after_key() -> None:
    """Test that inserting a dict after a key merges all pairs correctly."""
    m = _coll()
    base = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
    ins = OrderedDict([("x", 10), ("y", 20)])
    out = m.insert_dict_after(base, ins, "b")
    assert list(out.items()) == [
        ("a", 1),
        ("b", 2),
        ("x", 10),
        ("y", 20),
        ("c", 3),
    ]


def test_insert_dict_after_no_match_keeps_original() -> None:
    """Test that inserting a dict after a non-existent key keeps the original dict unchanged."""  # noqa: E501
    m = _coll()
    base = OrderedDict([("a", 1), ("b", 2)])
    ins = OrderedDict([("x", 10)])
    out = m.insert_dict_after(base, ins, "zzz")
    assert list(out.items()) == [("a", 1), ("b", 2)]
