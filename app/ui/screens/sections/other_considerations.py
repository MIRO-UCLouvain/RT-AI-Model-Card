"""Other Considerations page for the Model Cards Writing Tool."""

from __future__ import annotations

from typing import Any, TypedDict, cast

import streamlit as st

from app.services import schema_loader
from app.ui.forms.render import FieldProps, render_field
from app.ui.utils.typography import title

TITLE = "Other considerations"
SECTION_PREFIX = "other_considerations"


class OtherConsiderations(TypedDict, total=False):
    """
    TypedDict for the 'Other Considerations' section.

    :param TypedDict: The base class for TypedDicts
    :type TypedDict: type
    :param total: If True, all fields are required, defaults to False
    :type total: bool, optional
    """

    responsible_use_and_ethical_considerations: FieldProps
    risk_analysis: FieldProps
    post_market_surveillance_live_monitoring: FieldProps


def _render_fields(section: OtherConsiderations) -> None:
    render_field(
        "responsible_use_and_ethical_considerations",
        section["responsible_use_and_ethical_considerations"],
        SECTION_PREFIX,
    )
    render_field(
        "risk_analysis",
        section["risk_analysis"],
        SECTION_PREFIX,
    )
    render_field(
        "post_market_surveillance_live_monitoring",
        section["post_market_surveillance_live_monitoring"],
        SECTION_PREFIX,
    )


def _render_navigation() -> None:
    """Render the navigation buttons."""
    st.markdown("<br>", unsafe_allow_html=True)
    col1, _ = st.columns([2, 12])
    with col1:
        if st.button("Previous"):
            from app.ui.screens.sections.evaluation_data_mrc import (  # noqa: PLC0415
                evaluation_data_mrc_render,
            )

            st.session_state.runpage = evaluation_data_mrc_render
            st.rerun()


def other_considerations_render() -> None:
    """Render the Other Considerations page."""
    from app.ui.components.sidebar import sidebar_render  # noqa: PLC0415

    sidebar_render()

    schema_any: dict[str, Any] = schema_loader.get_model_card_schema()
    section = cast("OtherConsiderations", schema_any[SECTION_PREFIX])

    title(TITLE)
    _render_fields(section)
    _render_navigation()
