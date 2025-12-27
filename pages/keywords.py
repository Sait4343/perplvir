"""
Сторінка управління запитами
"""

import streamlit as st
import pandas as pd
from database import db, get_project_keywords, create_keywords
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
    df = df[["id", "keyword_text", "created_at", "is_active"]]
    df.columns = ["ID", "Запит", "Створено", "Активний"]

    # Selection
    selected_rows = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-row",
        on_select="rerun",
        key="keywords_table"
    )

    if selected_rows and len(selected_rows["selection"]["rows"]) > 0:
        selected_kws = [keywords[i]["keyword_text"] for i in selected_rows["selection"]["rows"]]

        st.markdown(f"**Обрано:** {len(selected_kws)} запитів")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶️ Запустити аналіз", type="primary"):
                with st.spinner("Запуск..."):
                    success = n8n_trigger_analysis(
                        project["id"],
                        selected_kws,
                        project["brand_name"],
                        ["Google Gemini"]
                    )
                    if success:
                        st.success("Аналіз запущено!")
