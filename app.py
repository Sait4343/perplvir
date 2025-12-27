"""
Virshi AI Visibility Platform - Модульна архітектура
"""

import streamlit as st
from auth import initialize_session_state, check_session, render_login_page, logout
from database import db
from pages.dashboard import render_dashboard
from pages.keywords import render_keywords_page
from pages.sources import render_sources_page
from pages.competitors import render_competitors_page
from pages.reports import render_reports_page
from pages.onboarding import render_onboarding

# Config
st.set_page_config(
    page_title="Virshi AI Visibility",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; }
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    .stButton>button { background-color: #8041F6; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #6a35cc; }
    div[data-testid="stMetric"] { background-color: #fff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Initialize
initialize_session_state()
check_session()

# Main Logic
if not st.session_state.get("user"):
    render_login_page()
else:
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/virshi-ai/image/39ba460ec649893b9495427aa102420beb1fa48d/virshi-op_logo-main.png", width=150)
        st.markdown("---")

        user_email = st.session_state["user"].email
        st.caption(f"**{st.session_state['role'].capitalize()}**")
        st.caption(user_email)
        st.markdown("---")

        # Project selector
        project = st.session_state.get("current_project")
        if project:
            st.markdown(f"**Проект:** {project['brand_name']}")

        st.markdown("### 🖥 Меню")

        # Navigation
        if st.button("🚀 Дашборд", use_container_width=True):
            st.session_state["current_page"] = "Дашборд"
            st.rerun()

        if st.button("📝 Запити", use_container_width=True):
            st.session_state["current_page"] = "Запити"
            st.rerun()

        if st.button("🔗 Джерела", use_container_width=True):
            st.session_state["current_page"] = "Джерела"
            st.rerun()

        if st.button("👥 Конкуренти", use_container_width=True):
            st.session_state["current_page"] = "Конкуренти"
            st.rerun()

        if st.button("📊 Звіти", use_container_width=True):
            st.session_state["current_page"] = "Звіти"
            st.rerun()

        st.markdown("---")

        if st.button("🚪 Вийти"):
            logout()

    # Main content
    current_page = st.session_state.get("current_page", "Дашборд")

    if not project:
        render_onboarding()
    else:
        if current_page == "Дашборд":
            render_dashboard()
        elif current_page == "Запити":
            render_keywords_page()
        elif current_page == "Джерела":
            render_sources_page()
        elif current_page == "Конкуренти":
            render_competitors_page()
        elif current_page == "Звіти":
            render_reports_page()
