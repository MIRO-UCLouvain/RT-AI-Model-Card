"""Reset-password screen — rendered at ?view=reset_password&token=<raw_token>."""

from __future__ import annotations

import streamlit as st

from app.client.model_cards import BackendError, reset_password

_MIN_PASSWORD_LENGTH = 8


def reset_password_page() -> None:
    """Render the reset-password form.

    Reads the one-time token from the ``token`` query parameter.
    Shows a clear error if the token is missing or already invalid before
    the user even submits the form.
    """
    # Read token from query params — Streamlit preserves all params on rerun.
    token: str = (st.query_params.get("token") or "").strip()

    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([0.6, 2, 0.6])
    with col:
        with st.container(border=True):
            st.header("Choose a new password")

            if not token:
                st.error(
                    "This reset link is missing a token. "
                    "Please use the link from your email, or request a new one."
                )
                st.markdown(
                    "[Request a new link](?view=forgot_password)",
                    unsafe_allow_html=True,
                )
                return

            with st.form("form_reset_password"):
                new_password = st.text_input(
                    f"New password (min {_MIN_PASSWORD_LENGTH} characters)",
                    type="password",
                    key="reset_pw_new",
                )
                confirm_password = st.text_input(
                    "Confirm new password",
                    type="password",
                    key="reset_pw_confirm",
                )
                submitted = st.form_submit_button(
                    "Reset password", use_container_width=True
                )

            if submitted:
                if not new_password or not confirm_password:
                    st.error("Please fill in both password fields.")
                elif len(new_password) < _MIN_PASSWORD_LENGTH:
                    st.error(
                        f"Password must be at least "
                        f"{_MIN_PASSWORD_LENGTH} characters."
                    )
                elif new_password != confirm_password:
                    st.error("Passwords do not match. Please try again.")
                else:
                    try:
                        reset_password(token, new_password)
                        st.success(
                            "Your password has been reset successfully. "
                            "You can now sign in with your new password."
                        )
                        st.markdown(
                            "[Go to login](?view=login)",
                            unsafe_allow_html=True,
                        )
                    except BackendError as exc:
                        error_msg = str(exc)
                        # Map backend generic message to a user-friendly hint.
                        if "invalid" in error_msg.lower() or "expired" in error_msg.lower():
                            st.error(
                                "This reset link is invalid or has expired. "
                                "Please request a new one."
                            )
                            st.markdown(
                                "[Request a new link](?view=forgot_password)",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error(
                                "Something went wrong. Please try again or "
                                "request a new reset link."
                            )

    st.markdown("---")
    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button(
            "← Back to Login",
            key="reset_pw_back_login",
            use_container_width=True,
        ):
            st.query_params["view"] = "login"
            st.rerun()
