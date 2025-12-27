"""
Майстер створення проекту
"""

import streamlit as st
import time
from database import create_project, create_keywords
from n8n.webhooks import n8n_generate_prompts, n8n_trigger_analysis

def render_onboarding():
    st.markdown("## 🚀 Налаштування Проекту")

    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = 1

    step = st.session_state["onboarding_step"]

    with st.container(border=True):
        # STEP 1: Input
        if step == 1:
            st.subheader("Крок 1: Дані про бренд")

            col1, col2 = st.columns(2)
            with col1:
                brand = st.text_input("Назва бренду", value=st.session_state.get("temp_brand", ""))
                industry = st.text_input("Галузь", value=st.session_state.get("temp_industry", ""))
            with col2:
                domain = st.text_input("Домен", value=st.session_state.get("temp_domain", ""))
                region = st.selectbox("Регіон", ["Ukraine", "USA", "Europe", "Global"])

            products = st.text_area("Продукти/Послуги", value=st.session_state.get("temp_products", ""))

            if st.button("Згенерувати запити"):
                if brand and domain and industry and products:
                    st.session_state.update({
                        "temp_brand": brand,
                        "temp_domain": domain,
                        "temp_industry": industry,
                        "temp_products": products,
                        "temp_region": region
                    })

                    with st.spinner("Генерація..."):
                        prompts = n8n_generate_prompts(brand, domain, industry, products)
                        if prompts:
                            st.session_state["generated_prompts"] = prompts
                            st.session_state["onboarding_step"] = 2
                            st.rerun()
                else:
                    st.warning("Заповніть всі поля")

        # STEP 2: Review & Launch
        elif step == 2:
            st.subheader("Крок 2: Перевірка та запуск")

            prompts = st.session_state.get("generated_prompts", [])

            if not prompts:
                st.warning("Список порожній")
                if st.button("Назад"):
                    st.session_state["onboarding_step"] = 1
                    st.rerun()
                return

            selected_kws = []
            for i, kw in enumerate(prompts):
                if st.checkbox(kw, value=True, key=f"kw_{i}"):
                    selected_kws.append(kw)

            st.divider()
            st.markdown(f"**Готово:** {len(selected_kws)} запитів")

            if st.button("🚀 Створити проект", type="primary"):
                if selected_kws:
                    user_id = st.session_state["user"].id
                    brand_name = st.session_state["temp_brand"]
                    domain_name = st.session_state["temp_domain"]
                    region_val = st.session_state.get("temp_region", "Ukraine")

                    # Create project
                    new_project = create_project(user_id, brand_name, domain_name, region_val)

                    if new_project:
                        st.session_state["current_project"] = new_project

                        # Add keywords
                        create_keywords(new_project["id"], selected_kws)

                        # Trigger analysis
                        progress = st.progress(0)
                        for i, kw in enumerate(selected_kws):
                            progress.progress((i + 1) / len(selected_kws))
                            n8n_trigger_analysis(
                                new_project["id"],
                                [kw],
                                brand_name,
                                ["Google Gemini"]
                            )
                            time.sleep(0.5)

                        st.success("Проект створено!")
                        st.session_state["onboarding_step"] = 1
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Оберіть хоча б один запит")
