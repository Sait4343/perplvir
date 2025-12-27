"""
Project creation wizard
"""

import streamlit as st
import time
from database import create_project, create_keywords, add_official_asset
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
                brand = st.text_input("Назва бренду", placeholder="Monobank", value=st.session_state.get("temp_brand", ""))
                industry = st.text_input("Галузь", placeholder="Фінтех", value=st.session_state.get("temp_industry", ""))
            with col2:
                domain = st.text_input("Домен", placeholder="monobank.ua", value=st.session_state.get("temp_domain", ""))
                region_options = ["Ukraine", "USA", "Europe", "Global"]
                saved_region = st.session_state.get("temp_region", "Ukraine")
                try:
                    idx = region_options.index(saved_region)
                except:
                    idx = 0
                region = st.selectbox("Регіон", options=region_options, index=idx)

            products = st.text_area("Продукти/Послуги", placeholder="Банківські картки, депозити", value=st.session_state.get("temp_products", ""))

            if st.button("Згенерувати запити", type="primary"):
                if brand and domain and industry and products:
                    st.session_state.update({
                        "temp_brand": brand,
                        "temp_domain": domain,
                        "temp_industry": industry,
                        "temp_products": products,
                        "temp_region": region
                    })

                    with st.spinner("Генерація запитів..."):
                        prompts = n8n_generate_prompts(brand, domain, industry, products)
                        if prompts:
                            st.session_state["generated_prompts"] = prompts
                            st.session_state["onboarding_step"] = 2
                            st.rerun()
                        else:
                            st.error("Не вдалося згенерувати запити")
                else:
                    st.warning("⚠️ Заповніть всі поля")

        # STEP 2: Review & Launch
        elif step == 2:
            st.subheader("Крок 2: Перевірка та запуск")

            prompts = st.session_state.get("generated_prompts", [])

            if not prompts:
                st.warning("Список порожній")
                if st.button("← Назад"):
                    st.session_state["onboarding_step"] = 1
                    st.rerun()
                return

            st.markdown("Оберіть запити для аналізу:")
            st.markdown("---")

            selected_kws = []
            for i, kw in enumerate(prompts):
                col_chk, col_num, col_text = st.columns([0.5, 0.5, 10])
                with col_chk:
                    if st.checkbox("", value=True, key=f"kw_check_{i}"):
                        selected_kws.append(kw)
                with col_num:
                    st.markdown(f'<div class="green-number-small">{i+1}</div>', unsafe_allow_html=True)
                with col_text:
                    st.markdown(f"**{kw}**")

            st.divider()
            st.markdown(f"**Готово до запуску:** {len(selected_kws)} запитів")

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("← Назад"):
                    st.session_state["onboarding_step"] = 1
                    st.rerun()

            with col2:
                if st.button("🚀 Створити проект та запустити", type="primary", use_container_width=True):
                    if selected_kws:
                        try:
                            user_id = st.session_state["user"].id
                            brand_name = st.session_state["temp_brand"]
                            domain_name = st.session_state["temp_domain"]
                            region_val = st.session_state.get("temp_region", "Ukraine")

                            # Create project
                            new_project = create_project(user_id, brand_name, domain_name, region_val)

                            if new_project:
                                st.session_state["current_project"] = new_project
                                proj_id = new_project["id"]

                                # Add official domain
                                clean_domain = domain_name.replace("https://", "").replace("http://", "").strip().rstrip("/")
                                try:
                                    add_official_asset(proj_id, clean_domain, "website")
                                except:
                                    pass

                                # Add keywords
                                create_keywords(proj_id, selected_kws)

                                # Trigger analysis
                                progress = st.progress(0, text="Ініціалізація...")
                                for i, kw in enumerate(selected_kws):
                                    progress.progress((i + 1) / len(selected_kws), text=f"Аналіз: {kw[:30]}...")
                                    n8n_trigger_analysis(
                                        proj_id,
                                        [kw],
                                        brand_name,
                                        ["Google Gemini"]
                                    )
                                    time.sleep(0.5)

                                progress.progress(1.0, text="✅ Готово!")
                                time.sleep(1)

                                st.session_state["onboarding_step"] = 1
                                st.session_state["current_page"] = "Дашборд"
                                st.success("Проект створено успішно!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Не вдалося створити проект")
                        except Exception as e:
                            st.error(f"Помилка: {e}")
                    else:
                        st.warning("Оберіть хоча б один запит")
