"""Module for license integration with Hugging Face."""
from __future__ import annotations

import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)
def get_cached_data() -> dict[str, str]:
    """
    Get cached license data from Hugging Face.

    :return: A dictionary mapping model names to their license identifiers.
    :rtype: dict[str, str]
    """
    license_df = pd.read_html(
        "https://huggingface.co/docs/hub/repositories-licenses",
    )[0]
    return pd.Series(
        license_df["License identifier (to use in repo card)"].values,
        index=license_df.Fullname,
    ).to_dict()
