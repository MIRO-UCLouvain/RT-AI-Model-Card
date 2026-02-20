"""Register screen — polished centered card at ?view=register."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.client.model_cards import BackendError, login, register
from app.ui.utils.auth import save_auth_and_redirect
from app.ui.utils.css import inject_css

AUTH_CSS = Path(__file__).resolve().parent.parent / "static" / "auth.css"

_COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahrain", "Bangladesh", "Belarus", "Belgium", "Bolivia",
    "Bosnia and Herzegovina", "Brazil", "Bulgaria", "Cambodia", "Cameroon",
    "Canada", "Chile", "China", "Colombia", "Costa Rica",
    "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Estonia",
    "Ethiopia", "Finland", "France", "Georgia", "Germany",
    "Ghana", "Greece", "Guatemala", "Honduras", "Hong Kong",
    "Hungary", "Iceland", "India", "Indonesia", "Iran",
    "Iraq", "Ireland", "Israel", "Italy", "Jamaica",
    "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait",
    "Latvia", "Lebanon", "Libya", "Lithuania", "Luxembourg",
    "Malaysia", "Malta", "Mexico", "Moldova", "Monaco",
    "Mongolia", "Montenegro", "Morocco", "Mozambique", "Nepal",
    "Netherlands", "New Zealand", "Nicaragua", "Nigeria", "North Macedonia",
    "Norway", "Oman", "Pakistan", "Panama", "Paraguay",
    "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Saudi Arabia", "Senegal", "Serbia",
    "Singapore", "Slovakia", "Slovenia", "South Africa", "South Korea",
    "Spain", "Sri Lanka", "Sweden", "Switzerland", "Taiwan",
    "Tanzania", "Thailand", "Tunisia", "Turkey", "UAE",
    "Uganda", "Ukraine", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Venezuela", "Vietnam", "Other",
]

# Inline SVG — user-plus icon (Feather-style)
_USER_PLUS_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>'
    '<circle cx="8.5" cy="7" r="4"/>'
    '<line x1="20" y1="8" x2="20" y2="14"/>'
    '<line x1="23" y1="11" x2="17" y2="11"/>'
    '</svg>'
)


def register_page() -> None:
    """Render the polished registration card."""
    inject_css(AUTH_CSS)

    # Same pattern as login_page: collect auth data inside the container,
    # then call save_auth() outside to avoid components.html rendering artifacts.
    _auth_result: tuple | None = None

    _, col, _ = st.columns([1, 2.5, 1])
    with col:
        with st.container(border=True):
            # ── Header ───────────────────────────────────────────────────
            st.markdown(
                '<div class="auth-header">'
                f'<div class="auth-header__icon">{_USER_PLUS_SVG}</div>'
                '<h2 class="auth-header__title">Create Account</h2>'
                '<p class="auth-header__subtitle">Join the AID-RT Model Card community</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            with st.form("form_register_page"):
                col_fn, col_ln = st.columns(2)
                with col_fn:
                    first_name = st.text_input(
                        "First Name", key="reg_page_first_name",
                        placeholder="Jane",
                    )
                with col_ln:
                    last_name = st.text_input(
                        "Last Name", key="reg_page_last_name",
                        placeholder="Doe",
                    )
                email = st.text_input(
                    "Email", key="reg_page_email",
                    placeholder="you@example.com",
                )
                institution = st.text_input(
                    "Institution / Company", key="reg_page_institution",
                    placeholder="e.g. University Hospital Brussels",
                )
                country = st.selectbox(
                    "Country",
                    options=[""] + _COUNTRIES,
                    index=0,
                    key="reg_page_country",
                    format_func=lambda x: "Select your country" if x == "" else x,
                )
                password = st.text_input(
                    "Password (min 8 characters)",
                    type="password",
                    key="reg_page_pass",
                    placeholder="Choose a strong password",
                )
                submitted = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if submitted:
                if not first_name or not last_name or not email or not password:
                    st.error("Please fill in all fields.")
                elif not institution or not institution.strip():
                    st.error("Please enter your institution or company.")
                elif not country:
                    st.error("Please select your country.")
                else:
                    try:
                        register(
                            email.strip(),
                            password,
                            first_name.strip(),
                            last_name.strip(),
                            institution=institution.strip(),
                            country=country,
                        )
                        # Auto-login after registration
                        result = login(email.strip(), password)
                        _auth_result = (
                            result["access_token"],
                            email.strip(),
                            first_name.strip(),
                            last_name.strip(),
                        )
                        st.query_params["view"] = "home"
                    except BackendError as exc:
                        st.error(str(exc))

            # ── Footer ───────────────────────────────────────────────────
            st.markdown(
                '<div class="auth-footer">'
                "Already have an account? "
                "<a href='?view=login'>Sign in</a>"
                '</div>',
                unsafe_allow_html=True,
            )

    # Set cookies and redirect.
    if _auth_result:
        save_auth_and_redirect(
            _auth_result[0], _auth_result[1],
            first_name=_auth_result[2], last_name=_auth_result[3],
            redirect_url="?view=home",
        )
        st.query_params["view"] = "home"
        st.rerun()

    _, col_back, _ = st.columns([1, 2, 1])
    with col_back:
        if st.button("← Back to Main Page", key="register_back_home", use_container_width=True):
            st.query_params["view"] = "home"
            st.rerun()
