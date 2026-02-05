"""Unit tests for backend/services/diff.py.

No database, no HTTP — pure logic tests.
"""

from __future__ import annotations

import pytest

from services.diff import compute_diff


# ── Helpers ───────────────────────────────────────────────────────────────────

def _only(diff: dict, section: str, bucket: str) -> list:
    return diff.get(section, {}).get(bucket, [])


def _fields(entries: list) -> set[str]:
    return {e["field"] for e in entries}


# ── Identical content ────────────────────────────────────────────────────────

def test_identical_returns_empty() -> None:
    content = {
        "card_metadata": {"version_number": "1.0", "doi": "10.1234/abc"},
        "model_basic_information": {"name": "MyModel"},
    }
    assert compute_diff(content, content) == {}


def test_empty_strings_equal_none() -> None:
    """Empty strings and None are semantically the same — no diff expected."""
    old = {"card_metadata": {"doi": ""}}
    new = {"card_metadata": {"doi": None}}
    assert compute_diff(old, new) == {}


# ── Flat section changes ──────────────────────────────────────────────────────

def test_added_field_in_section() -> None:
    old = {"card_metadata": {"version_number": "1.0"}}
    new = {"card_metadata": {"version_number": "1.0", "doi": "10.1234/x"}}
    diff = compute_diff(old, new)
    assert "card_metadata" in diff
    assert _fields(_only(diff, "card_metadata", "added")) == {"doi"}
    assert _only(diff, "card_metadata", "removed") == []
    assert _only(diff, "card_metadata", "changed") == []


def test_removed_field_in_section() -> None:
    old = {"card_metadata": {"version_number": "1.0", "doi": "10.1234/x"}}
    new = {"card_metadata": {"version_number": "1.0"}}
    diff = compute_diff(old, new)
    assert _fields(_only(diff, "card_metadata", "removed")) == {"doi"}


def test_changed_field_in_section() -> None:
    old = {"card_metadata": {"version_number": "1.0"}}
    new = {"card_metadata": {"version_number": "2.0"}}
    diff = compute_diff(old, new)
    changed = _only(diff, "card_metadata", "changed")
    assert len(changed) == 1
    assert changed[0]["field"] == "version_number"
    assert changed[0]["old"] == "1.0"
    assert changed[0]["new"] == "2.0"


# ── Entire section added / removed ────────────────────────────────────────────

def test_entire_section_added() -> None:
    old: dict = {}
    new = {"other_considerations": {"risk_analysis": "Low"}}
    diff = compute_diff(old, new)
    assert "other_considerations" in diff
    assert _only(diff, "other_considerations", "added") != []


def test_entire_section_removed() -> None:
    old = {"other_considerations": {"risk_analysis": "Low"}}
    new: dict = {}
    diff = compute_diff(old, new)
    assert "other_considerations" in diff
    assert _only(diff, "other_considerations", "removed") != []


# ── List fields ───────────────────────────────────────────────────────────────

def test_list_item_added() -> None:
    old = {"technical_specifications": {"model_inputs": ["CT"]}}
    new = {"technical_specifications": {"model_inputs": ["CT", "MRI"]}}
    diff = compute_diff(old, new)
    added = _only(diff, "technical_specifications", "added")
    assert any("model_inputs" in e["field"] for e in added)


def test_list_item_removed() -> None:
    old = {"technical_specifications": {"model_inputs": ["CT", "MRI"]}}
    new = {"technical_specifications": {"model_inputs": ["CT"]}}
    diff = compute_diff(old, new)
    removed = _only(diff, "technical_specifications", "removed")
    assert any("model_inputs" in e["field"] for e in removed)


def test_list_item_changed() -> None:
    old = {"technical_specifications": {"model_inputs": ["CT"]}}
    new = {"technical_specifications": {"model_inputs": ["MRI"]}}
    diff = compute_diff(old, new)
    changed = _only(diff, "technical_specifications", "changed")
    assert any("model_inputs" in e["field"] for e in changed)


def test_list_identical_no_diff() -> None:
    content = {"technical_specifications": {"model_inputs": ["CT", "MRI"]}}
    assert compute_diff(content, content) == {}


# ── Nested list-of-dicts (learning_architectures) ────────────────────────────

def test_learning_architecture_changed() -> None:
    arch_old = [{"id": 0, "loss_function": "BCE", "batch_size": 16}]
    arch_new = [{"id": 0, "loss_function": "Dice", "batch_size": 16}]
    old = {"technical_specifications": {"learning_architectures": arch_old}}
    new = {"technical_specifications": {"learning_architectures": arch_new}}
    diff = compute_diff(old, new)
    changed = _only(diff, "technical_specifications", "changed")
    assert any("learning_architectures" in e["field"] for e in changed)


def test_learning_architecture_added_entry() -> None:
    arch_old = [{"id": 0, "loss_function": "BCE"}]
    arch_new = [{"id": 0, "loss_function": "BCE"}, {"id": 1, "loss_function": "Dice"}]
    old = {"technical_specifications": {"learning_architectures": arch_old}}
    new = {"technical_specifications": {"learning_architectures": arch_new}}
    diff = compute_diff(old, new)
    added = _only(diff, "technical_specifications", "added")
    assert any("learning_architectures" in e["field"] for e in added)


# ── Evaluations (top-level list) ──────────────────────────────────────────────

def test_evaluation_added() -> None:
    old: dict = {"evaluations": []}
    new = {"evaluations": [{"name": "eval1", "evaluation_date": "2024-01-01"}]}
    diff = compute_diff(old, new)
    assert "evaluations" in diff
    added = _only(diff, "evaluations", "added")
    assert added != []


def test_evaluation_changed_metric() -> None:
    old = {"evaluations": [{"name": "eval1", "dsc": 0.85}]}
    new  = {"evaluations": [{"name": "eval1", "dsc": 0.90}]}
    diff = compute_diff(old, new)
    changed = _only(diff, "evaluations", "changed")
    assert changed != []


# ── Multiple sections simultaneously ─────────────────────────────────────────

def test_multi_section_diff() -> None:
    old = {
        "card_metadata": {"version_number": "1.0"},
        "model_basic_information": {"name": "OldName"},
    }
    new = {
        "card_metadata": {"version_number": "2.0"},
        "model_basic_information": {"name": "OldName"},
        "other_considerations": {"risk_analysis": "Low"},
    }
    diff = compute_diff(old, new)
    assert "card_metadata" in diff          # version_number changed
    assert "model_basic_information" not in diff  # name unchanged
    assert "other_considerations" in diff   # new section


# ── Type-mismatch edge case ───────────────────────────────────────────────────

def test_type_mismatch_treated_as_changed() -> None:
    old = {"section": {"field": "string_value"}}
    new = {"section": {"field": {"nested": "dict"}}}
    diff = compute_diff(old, new)
    changed = _only(diff, "section", "changed")
    assert any(e["field"] == "field" for e in changed)


# ── Whitespace / normalisation ────────────────────────────────────────────────

def test_whitespace_only_string_equals_empty() -> None:
    """A field filled with spaces is not the same as empty — real change."""
    old = {"section": {"notes": ""}}
    new = {"section": {"notes": "  some text  "}}
    diff = compute_diff(old, new)
    changed = _only(diff, "section", "changed")
    assert any(e["field"] == "notes" for e in changed)
