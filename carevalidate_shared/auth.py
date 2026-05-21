"""
CareValidate Shared Authentication
Simple session-based login gate — no external packages required.
Production: replace with SSO/SAML via Streamlit Community Cloud or Okta.
"""
import hashlib
import streamlit as st

# Credentials — change before sharing externally
_USERS = {
    "david":   hashlib.sha256(b"ReferWell2026!").hexdigest(),
    "connor":  hashlib.sha256(b"CareValidate2026!").hexdigest(),
    "demo":    hashlib.sha256(b"Demo1234!").hexdigest(),
}

_LOGIN_CSS = """
<style>
.cv-login-wrap {
    max-width: 420px;
    margin: 80px auto 0;
    background: #0d1117;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 40px 36px 32px;
}
.cv-login-logo {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.cv-login-logo span { color: #3b82f6; }
.cv-login-sub {
    font-size: 12px;
    color: #475569;
    margin-bottom: 28px;
}
.cv-login-badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    border: 1px solid rgba(16,185,129,0.35);
    color: #10b981;
    background: rgba(16,185,129,0.08);
    margin-bottom: 24px;
}
</style>
"""

def check_auth() -> bool:
    """
    Call at the top of each app (after set_page_config).
    Returns True if authenticated. If False, renders login form and stops execution.
    """
    if st.session_state.get("_cv_authenticated"):
        return True

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown(
            '<div class="cv-login-wrap">'
            '<div class="cv-login-logo"><span>Care</span>Validate</div>'
            '<div class="cv-login-sub">Finance Suite · Restricted Access</div>'
            '<div class="cv-login-badge">● HIPAA-Compliant · Synthetic Data Only</div>',
            unsafe_allow_html=True,
        )

        username = st.text_input("Username", placeholder="your username", key="_cv_user")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="_cv_pass")

        if st.button("Sign In", use_container_width=True, type="primary"):
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if _USERS.get(username.strip().lower()) == hashed:
                st.session_state["_cv_authenticated"] = True
                st.session_state["_cv_username"] = username.strip().lower()
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown(
            '<div style="margin-top:20px;font-size:11px;color:#334155;text-align:center;">'
            'No PHI is processed · All data is synthetic<br>'
            'Contact <a href="mailto:crsavenas@crimson.ua.edu" style="color:#3b82f6;">Connor Savenas</a> for access'
            '</div></div>',
            unsafe_allow_html=True,
        )

    st.stop()
    return False


def current_user() -> str:
    """Returns the logged-in username, or 'guest'."""
    return st.session_state.get("_cv_username", "guest")


def logout_button():
    """Renders a small logout button — call inside sidebar."""
    user = current_user()
    st.sidebar.markdown(
        f'<div style="font-size:11px;color:#475569;margin-bottom:4px;">Signed in as <strong style="color:#94a3b8;">{user}</strong></div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Sign Out", key="_cv_logout"):
        st.session_state["_cv_authenticated"] = False
        st.session_state["_cv_username"] = ""
        st.rerun()
