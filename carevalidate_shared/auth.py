"""
CareValidate Shared Authentication
Simple session-based login gate — no external packages required.
Production: replace with SSO/SAML via Streamlit Community Cloud or Okta.

Credential setup (in priority order):
  1. Streamlit Cloud: add [credentials] table to .streamlit/secrets.toml
       [credentials]
       alice = "<sha256 hex of password>"
       bob   = "<sha256 hex of password>"
  2. Environment variables:
       CV_DEMO_USERNAME=demo
       CV_DEMO_PASSWORD_HASH=<sha256 hex>
  3. Fallback: demo / Demo1234! (prototype only — change before sharing)
"""
import os
import hashlib
import streamlit as st


def _load_users() -> dict:
    """Return {username: sha256_hex} from secrets or env vars."""
    # 1 — Streamlit secrets (Streamlit Cloud / local secrets.toml)
    try:
        creds = dict(st.secrets.get("credentials", {}))
        if creds:
            return creds
    except Exception:
        pass
    # 2 — Single-user env var pair
    env_user = os.environ.get("CV_DEMO_USERNAME", "").strip()
    env_hash = os.environ.get("CV_DEMO_PASSWORD_HASH", "").strip()
    if env_user and env_hash:
        return {env_user: env_hash}
    # 3 — Prototype fallback (demo account only)
    return {"demo": hashlib.sha256(b"Demo1234!").hexdigest()}


_LOGIN_CSS = """
<style>
@keyframes login-card-glow {
    0%, 100% { box-shadow: 0 0 0 1px rgba(59,130,246,0.15), 0 8px 40px rgba(0,0,0,0.6), 0 0 60px rgba(59,130,246,0.07); }
    50%       { box-shadow: 0 0 0 1px rgba(59,130,246,0.28), 0 8px 40px rgba(0,0,0,0.6), 0 0 80px rgba(59,130,246,0.13); }
}
.cv-login-outer {
    position: relative;
    background: radial-gradient(ellipse at 60% 0%, rgba(59,130,246,0.09) 0%, transparent 70%),
                radial-gradient(ellipse at 20% 80%, rgba(139,92,246,0.06) 0%, transparent 60%);
    padding-top: 60px;
    padding-bottom: 60px;
}
.cv-login-wrap {
    max-width: 420px;
    margin: 0 auto;
    background: #0d1117;
    border: 1px solid rgba(59,130,246,0.18);
    border-radius: 18px;
    padding: 44px 38px 36px;
    animation: login-card-glow 4s ease-in-out infinite;
}
.cv-login-logo {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}
.cv-login-logo span {
    color: #3b82f6;
    text-shadow: 0 0 20px rgba(59,130,246,0.5);
}
.cv-login-sub {
    font-size: 12px;
    color: #475569;
    margin-bottom: 28px;
}
.cv-login-badge {
    display: inline-block;
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid rgba(59,130,246,0.35);
    color: #60a5fa;
    background: rgba(59,130,246,0.08);
    margin-bottom: 28px;
    letter-spacing: 0.3px;
}
</style>
"""


def check_auth() -> bool:
    """
    Call at the top of each page (after set_page_config).
    Returns True if authenticated. If not, renders login form and stops execution.
    """
    if st.session_state.get("_cv_authenticated"):
        return True

    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown(
            '<div class="cv-login-outer">'
            '<div class="cv-login-wrap">'
            '<div class="cv-login-logo"><span>Care</span>Validate</div>'
            '<div class="cv-login-sub">Finance Suite · Restricted Access</div>'
            '<div class="cv-login-badge">Synthetic Data Only · No PHI · Prototype</div>',
            unsafe_allow_html=True,
        )

        username = st.text_input("Username", placeholder="your username", key="_cv_user")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="_cv_pass")

        if st.button("Sign In →", use_container_width=True, type="primary"):
            users = _load_users()
            hashed = hashlib.sha256(password.encode()).hexdigest()
            if users.get(username.strip().lower()) == hashed:
                st.session_state["_cv_authenticated"] = True
                st.session_state["_cv_username"] = username.strip().lower()
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown(
            '<div style="margin-top:22px;font-size:11px;color:#334155;text-align:center;line-height:1.8;">'
            'Synthetic data only · No PHI processed<br>'
            'Contact <a href="mailto:crsavenas@crimson.ua.edu" style="color:#3b82f6;text-decoration:none;">Connor Savenas</a> for access'
            '</div></div></div>',
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
