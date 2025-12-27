"""
Official sources page
"""

import streamlit as st
from database import get_official_assets, add_official_asset

def render_sources_page():
    st.title("🔗 Офіційні джерела")

    project = st.session_state.get("current_project")
    if not project:
        st.info("Створіть проект")
        return

    with st.expander("➕ Додати джерело"):
        new_url = st.text_input("URL або домен")
        asset_type = st.selectbox("Тип", ["website", "social", "marketplace"])
        if st.button("Додати"):
            if new_url:
                if add_official_asset(project["id"], new_url, asset_type):
                    st.success("Додано!")
                    st.rerun()

    st.divider()

    assets = get_official_assets(project["id"])

    if assets:
        st.markdown("### Список джерел")
        for i, asset in enumerate(assets):
            st.markdown(f"{i+1}. `{asset}`")
    else:
        st.info("Джерела відсутні")
