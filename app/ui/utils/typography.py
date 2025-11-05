"""Module with utility functions for Streamlit app UI components."""

import re

import streamlit as st


def create_helpicon(
    label: str,
    description: str,
    field_format: str,
    example: str,
    required: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """
    Create a help icon with a tooltip for a form field.

    :param label: The label for the form field.
    :type label: str
    :param description: A description of the form field.
    :type description: str
    :param field_format: The expected format for the form field.
    :type field_format: str
    :param example: An example of the form field input.
    :type example: str
    :param required: Whether the form field is required, defaults to False
    :type required: bool, optional
    """
    required_tag: str = (
        "<span style='color: black; font-size: 1.2em;'>*</span>"
        if required
        else ""
    )

    st.markdown(
        """
        <style>
        .tooltip-inline {
            display: inline-block;
            position: relative;
            margin-left: 6px;
            cursor: pointer;
            font-size: 1em;
            color: #999;
        }
        .tooltip-inline .tooltiptext {
            visibility: hidden;
            width: 320px;
            background-color: #f9f9f9;
            color: #333;
            text-align: left;
            border-radius: 6px;
            border: 1px solid #ccc;
            padding: 10px;
            position: absolute;
            top: 125%;
            left: 0;
            z-index: 10;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
            font-weight: normal;
            font-size: 0.95em;
            line-height: 1.4;
            white-space: normal;
            word-wrap: break-word;
            display: inline-block;
        }
        .tooltip-inline:hover .tooltiptext { visibility: visible; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tooltip_html: str = f"""
    <div style='margin-bottom: 0px; font-weight: 500; font-size: 0.98em;'>
        {label} {required_tag}
        <span class="tooltip-inline">ⓘ
            <span class="tooltiptext">
                <strong>Description:</strong> {description}<br><br>
                <strong>Format:</strong> {field_format}<br><br>
                <strong>Example(s):</strong> {example}
            </span>
        </span>
    </div>
    """
    st.markdown(tooltip_html, unsafe_allow_html=True)


def light_header(
    text: str,
    size: str = "16px",
    bottom_margin: str = "1em",
) -> None:
    """
    Renders a light header in the Streamlit app.

    :param text: The text to display in the header.
    :type text: str
    :param size: The font size of the header, defaults to "16px"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the header, defaults to "1em"
    :type bottom_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-weight: normal;
            color: #444;
            margin-bottom: {bottom_margin};
        '>
            {text}
        </div>
    """,
        unsafe_allow_html=True,
    )


def light_header_italics(
    text: str, size: str = "16px", bottom_margin: str = "1em",
) -> None:
    """
    Renders a light italic header in the Streamlit app.

    :param text: The text to display in the header.
    :type text: str
    :param size: The font size of the header, defaults to "16px"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the header, defaults to "1em"
    :type bottom_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-style: italic;
            font-weight: normal;
            color: #444;
            margin-bottom: {bottom_margin};
        '>
            {text}
        </div>
    """,
        unsafe_allow_html=True,
    )


def title_header(
    text: str,
    size: str = "1.2rem",
    bottom_margin: str = "1em",
    top_margin: str = "0.5em",
) -> None:
    """
    Renders a title header in the Streamlit app.

    :param text: The text to display in the header.
    :type text: str
    :param size: The font size of the header, defaults to "1.2rem"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the header, defaults to "1em"
    :type bottom_margin: str, optional
    :param top_margin: The top margin of the header, defaults to "0.5em"
    :type top_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-weight: 600;
            color: #333;
            margin-top: {top_margin};
            margin-bottom: {bottom_margin};
        '>{text}</div>
        """,
        unsafe_allow_html=True,
    )


def title_header_grey(
    text: str,
    size: str = "1.3rem",
    bottom_margin: str = "0.2em",
    top_margin: str = "0.5em",
) -> None:
    """
    Renders a title header in grey in the Streamlit app.

    :param text: The text to display in the header.
    :type text: str
    :param size: The font size of the header, defaults to "1.3rem"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the header, defaults to "0.2em"
    :type bottom_margin: str, optional
    :param top_margin: The top margin of the header, defaults to "0.5em"
    :type top_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-weight: 600;
            color: #6c757d;
            margin-top: {top_margin};
            margin-bottom: {bottom_margin};
        '>{text}</div>
        """,
        unsafe_allow_html=True,
    )


def title(
    text: str,
    size: str = "2rem",
    bottom_margin: str = "0.1em",
    top_margin: str = "0.4em",
) -> None:
    """
    Renders a title in the Streamlit app.

    :param text: The text to display in the title.
    :type text: str
    :param size: The font size of the title, defaults to "2rem"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the title, defaults to "0.1em"
    :type bottom_margin: str, optional
    :param top_margin: The top margin of the title, defaults to "0.4em"
    :type top_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-weight: 650;
            color: #222;
            margin-top: {top_margin};
            margin-bottom: {bottom_margin};
            text-align: justify;
        '>{text}</div>
        """,
        unsafe_allow_html=True,
    )


def subtitle(
    text: str,
    size: str = "1.05rem",
    bottom_margin: str = "0.8em",
    top_margin: str = "0.2em",
) -> None:
    """
    Renders a subtitle in the Streamlit app.

    :param text: The text to display in the subtitle.
    :type text: str
    :param size: The font size of the subtitle, defaults to "1.05rem"
    :type size: str, optional
    :param bottom_margin: The bottom margin of the subtitle,
        defaults to "0.8em"
    :type bottom_margin: str, optional
    :param top_margin: The top margin of the subtitle, defaults to "0.2em"
    :type top_margin: str, optional
    """
    st.markdown(
        f"""
        <div style='
            font-size: {size};
            font-weight: 400;
            color: #444;
            margin-top: {top_margin};
            margin-bottom: {bottom_margin};
            text-align: justify;
        '>{text}</div>
        """,
        unsafe_allow_html=True,
    )


def section_divider() -> None:
    """Renders a horizontal line divider in the Streamlit app."""
    st.markdown(
        (
            "<hr style='margin: 1.5em 0; border: none; "
            "border-top: 1px solid #ccc;'>"
        ),
        unsafe_allow_html=True,
    )


def strip_brackets(text: str) -> str:
    """
    Remove any text within parentheses from the given string.

    :param text: The input string from which to remove text within parentheses.
    :type text: str
    :return: The input string with text within parentheses removed.
    :rtype: str
    """
    return re.sub(r"\s*\(.*?\)", "", text).strip()


def enlarge_tab_titles(
    font_px: int,
    underline_px: int = 4,
    pad_y: int = 6,
) -> None:
    """
    Enlarge the font size and padding of tab titles in the Streamlit app.

    :param font_px: The font size of the tab titles.
    :type font_px: int
    :param underline_px: The height of the underline for the active
        tab, defaults to 4.
    :type underline_px: int, optional
    :param pad_y: The vertical padding of the tab titles, defaults to 6.
    :type pad_y: int, optional
    """
    st.markdown(
        f"""
    <style>
      [data-testid="stTabs"] button[role="tab"] {{
        font-size: {font_px}px !important;
        padding-top: {pad_y}px !important;
        padding-bottom: {pad_y}px !important;
        line-height: 1.2 !important;
      }}
      [data-testid="stTabs"] button[role="tab"] p {{
        font-size: {font_px}px !important;
      }}
      [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
        height: {underline_px}px !important;
      }}
      [data-testid="stTabs"] [data-baseweb="tab"] {{
        font-size: {font_px}px !important;
        padding-top: {pad_y}px !important;
        padding-bottom: {pad_y}px !important;
      }}
    </style>
    """,
        unsafe_allow_html=True,
    )
