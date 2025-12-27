"""
Virshi AI Visibility Platform
Модульна архітектура
"""

import streamlit as st
from config import CUSTOM_CSS
from auth import initialize_session_state, check_session, render_login_page, logout
from database import db, get_user_projects
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

# Apply CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

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

        user = st.session_state["user"]
        user_email = user.email
        user_role = st.session_state.get("role", "user")

        st.caption(f"**{user_role.capitalize()}**")
        st.caption(user_email)
        st.markdown("---")

        # Project selector
        projects = get_user_projects(user.id)
        st.session_state["projects"] = projects

        if projects:
            project_names = [p['brand_name'] for p in projects]
            current_p = st.session_state.get("current_project")

            default_index = 0
            if current_p:
                try:
                    default_index = project_names.index(current_p['brand_name'])
                except:
                    default_index = 0

            selected_project_name = st.selectbox(
                "Оберіть проект:",
                project_names,
                index=default_index,
                key="project_selector"
            )

            # Update current project if changed
            new_project = next((p for p in projects if p['brand_name'] == selected_project_name), None)
            if new_project and (not current_p or current_p['id'] != new_project['id']):
                st.session_state["current_project"] = new_project
                st.rerun()

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
        st.caption("Потрібна допомога?")
        st.markdown("📧 [hi@virshi.ai](mailto:hi@virshi.ai)")
        st.caption("© 2025 Virshi AI")

        if st.button("🚪 Вийти"):
            logout()

    # Main content
    project = st.session_state.get("current_project")
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
        else:
            render_dashboard()
