"""Register screen — centered form at ?view=register."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, login, register
from app.ui.utils.auth import save_auth


def register_page() -> None:
    """Render the centered registration form."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Create Account")

            with st.form("form_register_page"):
                email = st.text_input("Email", key="reg_page_email")
                password = st.text_input(
                    "Password (min 8 chars)",
                    type="password",
                    key="reg_page_pass",
                )
                submitted = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    try:
                        register(email.strip(), password)
                        # Auto-login after registration
                        result = login(email.strip(), password)
                        # save_auth persists to session state + browser cookie
                        save_auth(result["access_token"], email.strip())
                        st.query_params["view"] = "home"
                        st.rerun()
                    except BackendError as exc:
                        st.error(str(exc))

            st.markdown(
                "Already have an account? [Login](?view=login)",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="register_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
