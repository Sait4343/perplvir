import streamlit as st
from config import CUSTOM_CSS
from database import db
from auth import (
    initialize_session_state, check_session, 
    render_login_page, logout
)
from pages.onboarding import render_onboarding
from pages.dashboard import render_dashboard
from pages.keywords import render_keywords_page
from pages.sources import render_sources_page
from pages.competitors import render_competitors_page
from pages.reports import render_reports_page

# Конфігурація
st.set_page_config(
    page_title="AI Visibility by Virshi",
    page_icon="👁️",
    layout="wide"
)

# CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Підключення БД
try:
    db.initialize(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"❌ Помилка підключення БД: {e}")
    st.stop()

# Ініціалізація
initialize_session_state()
check_session()

# Роутинг
if not st.session_state["user"]:
    render_login_page()
else:
    # Sidebar
    with st.sidebar:
        st.image("URL_ВАШОГО_ЛОГО", width=150)
        st.markdown("---")
        
        # Вибір проекту
        from database import get_user_projects
        projects = get_user_projects(st.session_state["user"].id)
        
        if projects:
            project_names = [p['brand_name'] for p in projects]
            selected = st.selectbox("Проект:", project_names)
            st.session_state["current_project"] = next(
                p for p in projects if p['brand_name'] == selected
            )
        
        st.markdown("---")
        
        # Меню
        page = st.radio(
            "Меню",
            ["🚀 Дашборд", "📝 Запити", "🔗 Джерела", 
             "👥 Конкуренти", "📊 Звіти"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("➕ Новий проект", use_container_width=True):
            st.session_state["current_page"] = "Онбординг"
            st.rerun()
        
        if st.button("🚪 Вийти", use_container_width=True):
            logout()
    
    # Рендеринг сторінок
    if st.session_state.get("current_page") == "Онбординг":
        render_onboarding()
    elif "Дашборд" in page:
        render_dashboard()
    elif "Запити" in page:
        render_keywords_page()
    elif "Джерела" in page:
        render_sources_page()
    elif "Конкуренти" in page:
        render_competitors_page()
    elif "Звіти" in page:
        render_reports_page()
