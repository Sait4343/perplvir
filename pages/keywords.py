"""
Keywords management page
"""

import streamlit as st
import pandas as pd
from database import get_project_keywords, create_keywords
from n8n.webhooks import n8n_trigger_analysis

def render_keywords_page():
    st.title("📝 Перелік запитів")

    project = st.session_state.get("current_project")
    if not project:
        st.info("Створіть проект")
        return

    # Add new keywords
    with st.expander("➕ Додати нові запити"):
        new_kw = st.text_area("Введіть запити (один на рядок)")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Додати", type="primary"):
                if new_kw:
                    kw_list = [k.strip() for k in new_kw.split("\n") if k.strip()]
                    if create_keywords(project["id"], kw_list):
                        st.success(f"Додано {len(kw_list)} запитів")
                        st.rerun()

    st.divider()

    # List keywords
    keywords = get_project_keywords(project["id"])

    if not keywords:
        st.info("Запити відсутні")
        return

    df = pd.DataFrame(keywords)
    df["selected"] = False

    st.markdown(f"**Всього запитів:** {len(keywords)}")

    # Simple table with checkboxes
    for i, kw in enumerate(keywords):
        col1, col2, col3 = st.columns([0.5, 8, 2])
        with col1:
            selected = st.checkbox("", key=f"kw_sel_{i}")
        with col2:
            st.markdown(f"**{kw['keyword_text']}**")
        with col3:
            st.caption(kw.get("created_at", "")[:10])

        if selected:
            if "selected_kws" not in st.session_state:
                st.session_state["selected_kws"] = []
            if kw['keyword_text'] not in st.session_state["selected_kws"]:
                st.session_state["selected_kws"].append(kw['keyword_text'])

    if "selected_kws" in st.session_state and st.session_state["selected_kws"]:
        st.divider()
        st.markdown(f"**Обрано:** {len(st.session_state['selected_kws'])}")

        if st.button("▶️ Запустити аналіз", type="primary"):
            with st.spinner("Запуск..."):
                success = n8n_trigger_analysis(
                    project["id"],
                    st.session_state["selected_kws"],
                    project["brand_name"],
                    ["Google Gemini"]
                )
                if success:
                    st.success("Аналіз запущено!")
                    st.session_state["selected_kws"] = []
