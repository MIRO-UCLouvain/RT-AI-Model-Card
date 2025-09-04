"""Module for rendering form fields."""

from __future__ import annotations

import html
import re
from collections.abc import Callable

# Sequence is only required for type annotations.
# Import it only while type-checking to avoid runtime cost.
from datetime import UTC, date, datetime
from typing import (
    TYPE_CHECKING,
    Literal,
    TypedDict,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

import numpy as np
import streamlit as st

from app.core.standards.tg263 import RTSTRUCT_SUBTYPES
from app.services.state_store import load_value, store_value
from app.services.uploads import (
    ALLOWED_UPLOAD_EXTS,
    bump_uploader,
    ensure_upload_state,
    field_current,
    field_delete,
    field_overwrite,
    uploader_key_for,
)
from app.ui.utils.typography import create_helpicon, strip_brackets

DEFAULT_SELECT = "-Select an option-"
DELETE_HINT = (
    "To remove the current file, use the **Delete** button below. "
    "The 'X' in the uploader is disabled."
)

# Named constant for the expected length of a YYYYMMDD date string.
DATE_STR_LEN = 8

FieldType = Literal["text", "select", "image", "date"]

class FieldProps(TypedDict, total=False):
    """
    Properties for a field in the schema.

    :param TypedDict: The base class for TypedDicts.
    :type TypedDict: type
    :param total: If True, all fields are required; if False,
        they are optional.
    :type total: bool, optional
    """

    label: str
    description: str
    example: str
    type: FieldType
    required: bool
    options: list[str]
    placeholder: str
    model_types: list[str]
    format: str
    format_description: str


def has_renderable_fields(
    field_keys: Sequence[str],
    schema_section: dict[str, FieldProps],
    current_task: str | None,
) -> bool:
    """
    Check if any of the specified field keys should be rendered.

    :param field_keys: The keys of the fields to check.
    :type field_keys: Sequence[str]
    :param schema_section: The schema section containing field definitions.
    :type schema_section: dict[str, FieldProps]
    :param current_task: The current task context, if any.
    :type current_task: Optional[str]
    :return: True if any of the specified field keys should be rendered,
        False otherwise.
    :rtype: bool
    """
    return any(
        key in schema_section
        and should_render(
            schema_section[key],
            current_task,
        )
        for key in field_keys
    )


def render_fields(
    field_keys: Sequence[str],
    schema_section: dict[str, FieldProps],
    section_prefix: str,
    current_task: str | None,
) -> None:
    """
    Render a list of fields guarded by ``should_render``
    using the function `render_field`.

    :param field_keys: The keys of the fields to render.
    :type field_keys: Sequence[str]
    :param schema_section: The schema section containing field definitions.
    :type schema_section: dict[str, FieldProps]
    :param section_prefix: The prefix to use for the field keys.
    :type section_prefix: str
    :param current_task: The current task context, if any.
    :type current_task: Optional[str]
    """  # noqa: D205
    for key in field_keys:
        if key in schema_section and should_render(
            schema_section[key],
            current_task,
        ):
            render_field(key, schema_section[key], section_prefix)


def should_render(props: FieldProps, current_task: str | None) -> bool:
    """
    Determine if a field should be rendered based on
    its properties and the current task.

    :param props: The properties of the field to check.
    :type props: FieldProps
    :param current_task: The current task context, if any.
    :type current_task: Optional[str]
    :return: True if the field should be rendered, False otherwise.
    :rtype: bool
    """  # noqa: D205
    model_types = props.get("model_types")
    if not model_types:
        return True
    if current_task:
        return current_task.strip().lower() in (m.lower() for m in model_types)
    return False


def _coerce_float_np(value: object, default: float = 0.0) -> float:
    """
    Converts a value to float using NumPy, returning default if invalid.

    :param value: The value to convert.
    :type value: object
    :param default: The default value to return if conversion fails,
        defaults to 0.0
    :type default: float, optional
    :return: The converted float value or the default.
    :rtype: float
    """
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return float(default)
        value = s
    try:
        out = float(np.asarray(value, dtype=float))
    except (TypeError, ValueError):
        out = float(default)
    if np.isnan(out) or np.isinf(out):
        return float(default)
    return out


def _fingerprint_uploaded(uploaded: object | None) -> tuple[str, int] | None:
    """
    Create a tiny fingerprint (name, size) so each selection is processed once.

    :param uploaded: The uploaded file object (or None).
    :type uploaded: object | None
    :return: A tuple containing the file name and size, or None if unavailable.
    :rtype: Optional[tuple[str, int]]
    """
    if uploaded is None:
        return None
    try:
        name = getattr(uploaded, "name", None)
        getbuf = getattr(uploaded, "getbuffer", None)
        if not callable(getbuf):
            return None
        buf = getbuf()
        size = len(buf) if buf is not None else 0
        return (str(name), int(size))
    except (AttributeError, TypeError, ValueError, OSError):
        return None


def render_image_field(
    key: str,
    props: FieldProps,
    section_prefix: str,
) -> None:
    """
    Render an always-visible image file uploader with delete/remount behavior.

    :param key: The key of the field.
    :type key: str
    :param props: The properties of the field.
    :type props: FieldProps
    :param section_prefix: The prefix to use for the field keys.
    :type section_prefix: str
    """
    full_key = f"{section_prefix}_{key}"
    token_key = (
        f"{full_key}__uploader_token"  # last processed selection fingerprint
    )

    ensure_upload_state()

    label = props.get("label") or key or "Field"
    description = props.get("description", "")
    example = props.get("example", "")
    field_type = props.get("type", "")
    required = bool(props.get("required", False))

    create_helpicon(label, description, field_type, example, required)

    st.markdown(
        "<i>If too big or not readable, please indicate the figure number "
        "and attach it to the appendix</i>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.text_input(
            label=".",
            placeholder="e.g., Fig. 1",
            key=f"{full_key}_appendix_note",
            label_visibility="collapsed",
        )

    with col2:
        uploaded = st.file_uploader(
            label=".",
            type=ALLOWED_UPLOAD_EXTS,
            key=uploader_key_for(full_key),  # key tied to a nonce
            label_visibility="collapsed",
        )

        # Save once per selection to keep uploader selection visible
        # (this preserves the uploader 'x' button)
        fp = _fingerprint_uploaded(uploaded)
        prev_fp = st.session_state.get(token_key)
        if uploaded is not None and fp is not None and fp != prev_fp:
            field_delete(full_key)
            field_overwrite(full_key, uploaded, "uploads")
            st.session_state[f"{full_key}_image"] = uploaded  # back-compat
            st.session_state[token_key] = fp
            st.rerun()

        existing = field_current(full_key)
        if existing:
            st.caption(f"Current file: **{existing['name']}**")
            st.info(DELETE_HINT)
            if st.button("Delete", key=f"{full_key}__remove_btn"):
                field_delete(full_key)
                # allow re-uploading same file
                st.session_state.pop(token_key, None)
                bump_uploader(full_key)  # remount clears the uploader safely
                st.rerun()
        else:
            st.caption("No file selected yet.")


Handler = Callable[[str, FieldProps, str], None]


def render_field(key: str, props: FieldProps, section_prefix: str) -> None:  # noqa: PLR0911
    """
    Render a field by dispatching to a specialized handler.

    :param key: The key of the field.
    :type key: str
    :param props: The properties of the field.
    :type props: FieldProps
    :param section_prefix: The prefix to use for the field keys.
    :type section_prefix: str
    """
    full_key = f"{section_prefix}_{key}"

    # 1) help icon
    label = props.get("label") or key or "Field"
    description = props.get("description", "")
    example = props.get("example", "")
    required = bool(props.get("required", False))
    create_helpicon(
        label,
        description,
        props.get("type", ""),
        example,
        required,
    )

    # 2) special key families with bespoke UIs
    if key == "type_metrics_other":
        _render_type_metrics_other(full_key)
        return

    if props.get("type") == "date":
        _render_date_input(full_key, props, key_name=key)
        return

    if key == "version_number" and section_prefix == "card_metadata":
        _render_version_number(full_key)
        return

    if props.get("type") == "select":
        if key in [
            "input_content",
            "output_content",
            "model_inputs",
            "model_outputs",
        ]:
            _render_content_list_select(full_key, props)
            return
        if key in ["treatment_modality_train", "treatment_modality_eval"]:
            _render_treatment_modality_select(full_key, props)
            return
        if key in ["type_ism", "type_gm_seg"]:
            _render_metric_select_list(full_key, props)
            return
        if key in ["type_dose_dm", "type_dose_dm_seg", "type_dose_dm_dp"]:
            _render_dose_metric_selector(full_key)
            return
        _render_simple_select(full_key, props)
        return

    # Fallback: text input
    _render_text_input(full_key, props)

    # 3) inline validation (kept behavior)
    _validate_format(full_key, props)


def _on_date_change(raw_key: str, widget_key: str, full_key: str) -> None:
    user_date: date | None = st.session_state.get(raw_key)
    st.session_state[widget_key] = user_date
    formatted = user_date.strftime("%Y%m%d") if user_date else None
    st.session_state[full_key] = formatted


def _render_date_input(
    full_key: str,
    props: FieldProps,  # noqa: ARG001
    key_name: str,  # noqa: ARG001
) -> None:
    widget_key = f"{full_key}_widget"
    raw_key = f"_{widget_key}"

    stored = st.session_state.get(full_key)
    initial_widget_date: date | None = None
    if (
        isinstance(stored, str)
        and len(stored) == DATE_STR_LEN
        and stored.isdigit()
    ):
        try:
            y, m, d = int(stored[:4]), int(stored[4:6]), int(stored[6:8])
            initial_widget_date = date(y, m, d)
        except ValueError:
            initial_widget_date = None
    elif isinstance(stored, date):
        initial_widget_date = stored

    def _on_change_wrapper() -> None:
        _on_date_change(raw_key, widget_key, full_key)

    if raw_key in st.session_state:
        st.date_input(
            "Click and select a date",
            min_value=date(1900, 1, 1),
            max_value=datetime.now(UTC).date(),
            key=raw_key,
            on_change=_on_change_wrapper,
        )
    else:
        st.date_input(
            "Click and select a date",
            value=initial_widget_date,
            min_value=date(1900, 1, 1),
            max_value=datetime.now(UTC).date(),
            key=raw_key,
            on_change=_on_change_wrapper,
        )

    user_date: date | None = st.session_state.get(raw_key)
    st.session_state[widget_key] = user_date
    st.session_state[full_key] = (
        user_date.strftime("%Y%m%d") if user_date else None
    )


def _render_version_number(full_key: str) -> None:
    """
    Renders a specialized number input for card_metadata.version_number.

    :param full_key: The full key of the field.
    :type full_key: str
    """
    load_value(full_key, default=0.0)

    widget_key = "_" + full_key
    current = st.session_state.get(
        widget_key,
        st.session_state.get(full_key, 0.0),
    )
    st.session_state[widget_key] = _coerce_float_np(current, 0.0)

    st.number_input(
        label=".",
        min_value=0.0,
        max_value=10_000_000_000.0,
        step=0.1,
        format="%.1f",
        key=widget_key,
        on_change=store_value,
        args=(full_key,),
        label_visibility="hidden",
    )


def _validate_format(full_key: str, props: FieldProps) -> None:
    """
    Validate the format of the input field.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    pattern = props.get("format")
    if not pattern:
        return
    value = st.session_state.get(full_key)
    if value is not None and not re.match(pattern, str(value)):
        friendly_msg = props.get("format_description") or "Invalid format."
        st.error(friendly_msg)


def _render_simple_select(full_key: str, props: FieldProps) -> None:
    """
    Render a simple select input.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    options = props.get("options", [])
    if not options:
        label_text = props.get("label") or full_key
        st.warning(
            f"Field '{label_text}' is missing options for select dropdown.",
        )
        return

    load_value(full_key)
    st.selectbox(
        props.get("label", full_key),
        options=options,
        key="_" + full_key,
        on_change=store_value,
        args=(full_key,),
        help=props.get("description", ""),
        label_visibility="hidden",
        placeholder=DEFAULT_SELECT,
    )


def _render_text_input(full_key: str, props: FieldProps) -> None:
    """
    Render a text input field.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    load_value(full_key)
    st.text_input(
        props.get("label", full_key),
        key="_" + full_key,
        on_change=store_value,
        args=(full_key,),
        label_visibility="hidden",
        placeholder=props.get("placeholder", ""),
    )


def _render_content_list_select(full_key: str, props: FieldProps) -> None:  # noqa: PLR0912, PLR0915
    """
    Render a content list select input.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    content_list_key = f"{full_key}_list"
    type_key = f"{full_key}_new_type"
    subtype_key = f"{full_key}_new_subtype"

    load_value(content_list_key, default=[])
    load_value(type_key)
    load_value(subtype_key)

    options = props.get("options", [])
    if st.session_state.get("_" + type_key) == "RTSTRUCT":
        col1, col2, col3 = st.columns([2, 1, 0.4])
        with col1:
            st.selectbox(
                label=".",
                options=options,
                key="_" + type_key,
                on_change=store_value,
                args=(type_key,),
                label_visibility="hidden",
                placeholder=DEFAULT_SELECT,
            )
        with col2:
            subtype_value = st.selectbox(
                label=".",
                options=[*RTSTRUCT_SUBTYPES, "Other"],
                key="_" + subtype_key,
                on_change=store_value,
                args=(subtype_key,),
                label_visibility="hidden",
                placeholder=DEFAULT_SELECT,
            )
            st.info(
                "If the structure name isn't in the dropdown menu, select "
                "**Other** and introduce the name manually.",
            )
            if subtype_value == "Other":
                custom_key = f"{subtype_key}_custom"
                load_value(custom_key, default="")
                st.text_input(
                    "Enter custom RTSTRUCT subtype",
                    value=st.session_state.get(custom_key, ""),
                    key=custom_key,
                    placeholder="Introduce custom value",
                )
        with col3:
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            if st.button("Add", key=f"{full_key}_add_button"):
                subtype = st.session_state.get(subtype_key, "")
                if subtype == "Other":
                    subtype = st.session_state.get(f"{subtype_key}_custom", "")
                entry = f"RTSTRUCT_{subtype}"
                st.session_state[content_list_key].append(entry)
                st.session_state[full_key] = st.session_state[content_list_key]
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns([2, 1, 0.5])
        with col1:
            st.selectbox(
                label=".",
                options=options,
                key="_" + type_key,
                on_change=store_value,
                args=(type_key,),
                label_visibility="hidden",
                placeholder=DEFAULT_SELECT,
            )
        selected_type = st.session_state.get(type_key)
        custom_key = f"{full_key}_custom_text"
        load_value(custom_key, default="")
        with col2:
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            if selected_type == "OT (Other)":
                st.text_input(
                    "Enter custom input",
                    value=st.session_state.get(custom_key, ""),
                    key=custom_key,
                    label_visibility="collapsed",
                    placeholder="Introduce custom value",
                )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("&nbsp;", unsafe_allow_html=True)
        with col3:
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            add_clicked = st.button("Add", key=f"{full_key}_add_button")
            st.markdown("</div>", unsafe_allow_html=True)
        if add_clicked:
            if selected_type in [None, "", DEFAULT_SELECT]:
                st.error("Please select an option before adding.")
            elif selected_type == "OT (Other)":
                custom_text = st.session_state.get(custom_key, "").strip()
                if not custom_text:
                    st.error("Please enter a custom name before adding.")
                else:
                    st.session_state[content_list_key].append(custom_text)
                    st.session_state[full_key] = st.session_state[
                        content_list_key
                    ]
            else:
                entry = strip_brackets(str(selected_type))
                st.session_state[content_list_key].append(entry)
                st.session_state[full_key] = st.session_state[content_list_key]

    _render_inline_tag_list(full_key, content_list_key)


def _render_treatment_modality_select(
    full_key: str,
    props: FieldProps,
) -> None:
    """
    Render a treatment modality select input.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    content_list_key2 = f"{full_key}_modality_list"
    type_key2 = f"{full_key}_modality_type"

    load_value(content_list_key2, default=[])
    load_value(type_key2)

    col1, col2 = st.columns([4, 0.5])
    with col1:
        st.selectbox(
            label=".",
            options=props.get("options", []),
            key="_" + type_key2,
            on_change=store_value,
            args=(type_key2,),
            label_visibility="hidden",
            placeholder=DEFAULT_SELECT,
        )
    with col2:
        st.markdown("<div style='margin-top: 26px;'>", unsafe_allow_html=True)
        add_clicked = st.button("Add", key=f"{full_key}_modality_add_button")
        st.markdown("</div>", unsafe_allow_html=True)

    raw_value2 = st.session_state.get(type_key2)
    if add_clicked:
        if raw_value2 in [None, "", DEFAULT_SELECT]:
            st.error("Please select an option before adding.")
        else:
            entry = strip_brackets(str(raw_value2))
            st.session_state[content_list_key2].append(entry)
            st.session_state[full_key] = st.session_state[content_list_key2]

    _render_inline_tag_list(
        full_key,
        content_list_key2,
        clear_key=f"{full_key}_modality_clear_all",
    )


def _render_metric_select_list(full_key: str, props: FieldProps) -> None:
    """
    Render a metric select input.

    :param full_key: The full key of the field.
    :type full_key: str
    :param props: The properties of the field.
    :type props: FieldProps
    """
    type_key = full_key + "_selected"
    type_list_key = full_key + "_list"
    load_value(type_key)
    load_value(type_list_key, default=[])

    col1, col2, col3 = st.columns([3.5, 0.5, 1])
    with col1:
        st.selectbox(
            label=props.get("label", full_key),
            options=props.get("options", []),
            key="_" + type_key,
            on_change=store_value,
            args=(type_key,),
            label_visibility="hidden",
            placeholder=DEFAULT_SELECT,
        )
    with col2:
        st.markdown("<div style='margin-top: 26px;'>", unsafe_allow_html=True)
        add_clicked = st.button("Add", key=f"{full_key}_add_button")
        st.markdown("</div>", unsafe_allow_html=True)

    if add_clicked:
        value = st.session_state.get(type_key)
        if not value:
            st.markdown(" ")
            st.error(
                "Please choose an image similarity metrics before adding.",
            )
        elif value not in st.session_state[type_list_key]:
            st.session_state[type_list_key].append(value)
            st.session_state[full_key] = st.session_state[type_list_key]

    with col3:
        if st.session_state[type_list_key]:
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            if st.button("Clear", key=f"{full_key}_clear_button"):
                st.session_state[type_list_key] = []
                st.session_state[full_key] = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _render_dose_metric_selector(full_key: str) -> None:  # noqa: C901, PLR0912, PLR0915
    """
    Render a dose metric select input.

    :param full_key: The full key of the field.
    :type full_key: str
    """
    static_options = [
        "GPR (Gamma Passing Rate)",
        "MAE (Mean Absolute Error)",
        "MSE (Mean Squared Error)",
        "Other",
    ]
    parametric_options = ["D", "V"]

    dm_key = full_key
    dm_list_key = f"{dm_key}_list"
    dm_select_key = f"{dm_key}_selected"
    dm_dynamic_key = f"{dm_key}_dyn"

    load_value(dm_list_key, default=[])
    load_value(dm_select_key)
    load_value(dm_dynamic_key, default={"prefix": "D", "value": 95})

    col1, col2, col3, col4 = st.columns([2, 2, 0.5, 0.5])
    with col1:
        st.selectbox(
            "Select dose metric",
            options=static_options + parametric_options,
            key="_" + dm_select_key,
            on_change=store_value,
            args=(dm_select_key,),
            label_visibility="hidden",
            placeholder=DEFAULT_SELECT,
        )
        dm_type = st.session_state[dm_select_key]

    with col2:
        val: int | str | None = None
        if dm_type in parametric_options:
            val_key = f"{dm_dynamic_key}_{dm_type}_value"
            if val_key not in st.session_state:
                st.session_state[val_key] = st.session_state[dm_dynamic_key][
                    "value"
                ]
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            val = st.number_input(
                f"{dm_type} value",
                min_value=1,
                max_value=100,
                value=st.session_state[val_key],
                key=val_key,
                label_visibility="collapsed",
                placeholder=f"Enter {dm_type} value",
            )
            st.markdown("</div>", unsafe_allow_html=True)
            st.session_state[dm_dynamic_key] = {
                "prefix": dm_type,
                "value": val,
            }
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            val = st.text_input(
                label="Other dose metric",
                label_visibility="collapsed",
                placeholder="Enter custom name",
                key=f"{dm_key}_other_text",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div style='margin-top: 26px;'>", unsafe_allow_html=True)
        add_clicked = st.button("Add", key=f"{dm_key}_add_button")
        st.markdown("</div>", unsafe_allow_html=True)

    if add_clicked:
        metric: str | None = None
        if not dm_type:
            st.markdown(" ")
            st.error("Please choose a dose metric type before adding.")
        elif dm_type in static_options and dm_type != "Other":
            metric = dm_type
        elif dm_type == "Other":
            metric = (val or "").strip() if isinstance(val, str) else ""
            if not metric:
                st.markdown(" ")
                st.error("Please enter a custom name for the dose metric.")
        elif dm_type in parametric_options:
            val_struct = st.session_state.get(dm_dynamic_key, {})
            if not val_struct:
                st.markdown(" ")
                st.error("Please enter a value for the dose metric.")
            else:
                metric = f"{dm_type}{val_struct.get('value', '')}"
        if metric and metric not in st.session_state[dm_list_key]:
            st.session_state[dm_list_key].append(metric)
            st.session_state[dm_key] = st.session_state[dm_list_key]

    with col4:
        if st.session_state[dm_list_key]:
            st.markdown(
                "<div style='margin-top: 26px;'>",
                unsafe_allow_html=True,
            )
            if st.button("Clear", key=f"{dm_key}_clear_button"):
                st.session_state[dm_list_key] = []
                st.session_state[dm_key] = []
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _render_type_metrics_other(full_key: str) -> None:
    """
    Render a custom dose metric input for "Other" type-task.

    :param full_key: The full key of the field.
    :type full_key: str
    """
    metrics_list_key = f"{full_key}_list"
    metrics_selected_key = f"{full_key}_selected"

    load_value(metrics_list_key, default=[])
    load_value(metrics_selected_key)

    show_warning = False

    col1, col2, col3 = st.columns([3, 0.5, 1])
    with col1:
        st.text_input(
            label=".",
            key="_" + metrics_selected_key,
            on_change=store_value,
            args=(metrics_selected_key,),
            placeholder="Enter metric name (e.g. MSE)",
            label_visibility="hidden",
        )
    with col2:
        st.markdown("<div style='margin-top: 26px;'>", unsafe_allow_html=True)
        if st.button("Add", key=f"{full_key}_add_button"):
            value = st.session_state.get(metrics_selected_key, "")
            if value and value.strip():
                value = value.strip()
                if value not in st.session_state[metrics_list_key]:
                    st.session_state[metrics_list_key].append(value)
                    st.session_state[full_key] = st.session_state[
                        metrics_list_key
                    ]
                else:
                    show_warning = True
            else:
                show_warning = True
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='margin-top: 26px;'>", unsafe_allow_html=True)
        if st.button("Clear", key=f"{full_key}_clear_button"):
            st.session_state[metrics_list_key] = []
            st.session_state[full_key] = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if show_warning:
        st.warning("Please enter a valid metric name before adding.")


def _render_inline_tag_list(
    full_key: str,
    list_state_key: str,
    *,
    clear_key: str | None = None,
) -> None:
    """
    Render an inline tag list.

    :param full_key: The full key of the field.
    :type full_key: str
    :param list_state_key: The state key for the list.
    :type list_state_key: str
    :param clear_key: The state key for the clear button, defaults to None
    :type clear_key: Optional[str], optional
    """
    entries: list[str] = st.session_state.get(list_state_key, [])
    if not entries:
        return

    tooltip_items = [
        (
            f"<span title='{html.escape(item)}' "
            "style='margin-right: 6px; font-weight: 500; color: #333;'>"
            f"{html.escape(strip_brackets(item))}</span>"
        )
        for item in entries
    ]
    line = ", ".join(tooltip_items)
    st.markdown(f"<span>{line}</span>", unsafe_allow_html=True)

    if st.button("Clear", key=(clear_key or f"{full_key}_clear_all")):
        st.session_state[list_state_key] = []
        st.session_state[full_key] = []
        st.rerun()
