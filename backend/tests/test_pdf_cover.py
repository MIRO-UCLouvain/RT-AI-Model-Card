"""Unit tests for the PDF cover-page helpers in app/services/markdown/renderer.py.

Pure string functions — no database, no browser, no xhtml2pdf required.
"""

from __future__ import annotations

import pytest

from app.services.markdown.renderer import (
    _build_cover_html,
    _build_version_history_md,
    _html_esc,
)


# ── _html_esc ─────────────────────────────────────────────────────────────────

def test_html_esc_ampersand() -> None:
    assert _html_esc("a & b") == "a &amp; b"


def test_html_esc_less_than() -> None:
    assert _html_esc("a < b") == "a &lt; b"


def test_html_esc_greater_than() -> None:
    assert _html_esc("a > b") == "a &gt; b"


def test_html_esc_combined() -> None:
    assert _html_esc("<script>alert('x')</script>") == "&lt;script&gt;alert('x')&lt;/script&gt;"


def test_html_esc_clean_string_unchanged() -> None:
    assert _html_esc("plain text 123") == "plain text 123"


# ── _build_cover_html ─────────────────────────────────────────────────────────

@pytest.fixture()
def cover_basic() -> str:
    return _build_cover_html(
        model_name="MyModel",
        version="v2.1",
        author="Jane Doe",
        contact_email="jane@example.com",
        published_date="2025-06-01",
    )


def test_cover_contains_model_name(cover_basic: str) -> None:
    assert "MyModel" in cover_basic


def test_cover_contains_version(cover_basic: str) -> None:
    assert "v2.1" in cover_basic


def test_cover_contains_author(cover_basic: str) -> None:
    assert "Jane Doe" in cover_basic


def test_cover_contains_contact_email(cover_basic: str) -> None:
    assert "jane@example.com" in cover_basic


def test_cover_contains_published_date(cover_basic: str) -> None:
    assert "2025-06-01" in cover_basic


def test_cover_has_page_break() -> None:
    html = _build_cover_html("M", "v1", "A", "", "2025-01-01")
    assert "cover-break" in html


def test_cover_no_contact_row_when_empty() -> None:
    html = _build_cover_html(
        model_name="M",
        version="v1",
        author="Anon",
        contact_email="",
        published_date="2025-01-01",
    )
    assert "Contact" not in html


def test_cover_contact_row_present_when_given() -> None:
    html = _build_cover_html(
        model_name="M",
        version="v1",
        author="Anon",
        contact_email="test@test.com",
        published_date="2025-01-01",
    )
    assert "Contact" in html
    assert "test@test.com" in html


def test_cover_escapes_special_chars_in_name() -> None:
    html = _build_cover_html(
        model_name="My<Model>&Co",
        version="v1",
        author="A",
        contact_email="",
        published_date="2025-01-01",
    )
    assert "My&lt;Model&gt;&amp;Co" in html
    assert "My<Model>&Co" not in html


def test_cover_anonymous_fallback() -> None:
    html = _build_cover_html("M", "v1", "Anonymous", "", "2025-01-01")
    assert "Anonymous" in html


# ── _build_version_history_md ─────────────────────────────────────────────────

@pytest.fixture()
def versions_two() -> list[dict]:
    return [
        {"version": "v1.0", "created_at": "2024-01-15T10:00:00", "status": "published"},
        {"version": "v2.0", "created_at": "2024-06-20T10:00:00", "status": "published"},
    ]


def test_history_contains_header(versions_two: list) -> None:
    md = _build_version_history_md(versions_two)
    assert "## Version History" in md


def test_history_contains_versions(versions_two: list) -> None:
    md = _build_version_history_md(versions_two)
    assert "v1.0" in md
    assert "v2.0" in md


def test_history_contains_dates(versions_two: list) -> None:
    md = _build_version_history_md(versions_two)
    assert "2024-01-15" in md
    assert "2024-06-20" in md


def test_history_contains_status(versions_two: list) -> None:
    md = _build_version_history_md(versions_two)
    assert "Published" in md


def test_history_is_markdown_table(versions_two: list) -> None:
    md = _build_version_history_md(versions_two)
    assert "| Version |" in md
    assert "|---------|" in md


def test_history_sorted_by_version() -> None:
    versions = [
        {"version": "v3.0", "created_at": "2024-03-01", "status": "published"},
        {"version": "v1.0", "created_at": "2024-01-01", "status": "published"},
        {"version": "v2.0", "created_at": "2024-02-01", "status": "published"},
    ]
    md = _build_version_history_md(versions)
    pos_v1 = md.index("v1.0")
    pos_v2 = md.index("v2.0")
    pos_v3 = md.index("v3.0")
    assert pos_v1 < pos_v2 < pos_v3


def test_history_empty_list() -> None:
    md = _build_version_history_md([])
    assert "## Version History" in md
    # Table header still present but no data rows beyond the separator
    lines = [l for l in md.splitlines() if l.strip().startswith("|")]
    assert len(lines) == 2  # header + separator only


def test_history_replaces_underscore_in_status() -> None:
    versions = [{"version": "v1.0", "created_at": "2024-01-01", "status": "in_review"}]
    md = _build_version_history_md(versions)
    assert "In Review" in md
    assert "in_review" not in md
