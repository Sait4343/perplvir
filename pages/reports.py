"""
AI Reports page
"""

import streamlit as st
from n8n.webhooks import trigger_ai_recommendation

def render_reports_page():
    st.title("📊 AI Звіти")

    project = st.session_state.get("current_project")
    user = st.session_state.get("user")

    if not project:
        st.info("Створіть проект")
        return

    st.markdown("Оберіть категорію звіту:")

    categories = [
        "SEO & Content Strategy",
        "Brand Positioning Analysis",
        "Competitor Intelligence",
        "Custom Request"
    ]

    selected_category = st.selectbox("Категорія", categories)
    context = st.text_area("Додатковий контекст (опціонально)", height=100)

    if st.button("🚀 Згенерувати звіт", type="primary"):
        with st.spinner("Генерація звіту AI..."):
            html_report = trigger_ai_recommendation(
                user=user,
                project=project,
                category=selected_category,
                context_text=context
            )

            st.divider()
            st.markdown("### 📄 Результат")
            st.markdown(html_report, unsafe_allow_html=True)
