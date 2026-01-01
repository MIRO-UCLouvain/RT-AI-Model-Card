"""Forgot-password screen — centered form at ?view=forgot_password."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, forgot_password

_GENERIC_MESSAGE = (
    "If an account with that email exists, a reset link has been sent. "
    "Please check your inbox (and spam folder)."
)


def forgot_password_page() -> None:
    """Render the forgot-password form."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Forgot your password?")
            st.caption(
                "Enter your account email address and we will send you "
                "a link to reset your password."
            )

            with st.form("form_forgot_password"):
                email = st.text_input("Email address", key="forgot_pw_email")
                submitted = st.form_submit_button(
                    "Send reset link", use_container_width=True
                )

            if submitted:
                if not email or not email.strip():
                    st.error("Please enter your email address.")
                else:
                    try:
                        forgot_password(email.strip())
                        # Always show the same message — never reveal whether
                        # the address is registered.
                        st.success(_GENERIC_MESSAGE)
                    except BackendError:
                        # Even on backend errors show the generic message so
                        # that transient failures don't leak enumeration info.
                        st.success(_GENERIC_MESSAGE)

            st.markdown(
                "Remembered your password? [Sign in](?view=login)",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button(
            "← Back to Login",
            key="forgot_pw_back_login",
            use_container_width=True,
        ):
            st.query_params["view"] = "login"
            st.rerun()
