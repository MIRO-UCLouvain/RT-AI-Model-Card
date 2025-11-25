"""Login screen — centered form at ?view=login."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, login
from app.ui.utils.auth import save_auth


def login_page() -> None:
    """Render the centered login form."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Login")

            with st.form("form_login_page"):
                email = st.text_input("Email", key="login_page_email")
                password = st.text_input(
                    "Password", type="password", key="login_page_pass"
                )
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    try:
                        result = login(email.strip(), password)
                        # save_auth persists to session state + browser cookie
                        save_auth(result["access_token"], email.strip())
                        st.query_params["view"] = "home"
                        st.rerun()
                    except BackendError as exc:
                        st.error(str(exc))

            st.markdown(
                "No account? [Register](?view=register)", unsafe_allow_html=True
            )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="login_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
