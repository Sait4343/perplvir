"""
Онбординг: створення нового проекту
Оптимізація: прогрес-бар, валідація, batch operations
"""

import streamlit as st
import time
from typing import List
from database import create_project, add_keywords_batch, add_official_asset
from n8n.webhooks import n8n_generate_prompts, n8n_trigger_analysis
from components import render_green_number
from config import REGION_OPTIONS


def initialize_onboarding_state():
    """Ініціалізація стану онбордингу"""
    defaults = {
        "onboarding_step": 1,
        "generated_prompts": [],
        "temp_brand": "",
        "temp_domain": "",
        "temp_industry": "",
        "temp_products": "",
        "temp_region": "Ukraine"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def validate_step1_data(brand: str, domain: str, industry: str, 
                       products: str) -> tuple[bool, str]:
    """
    Валідація даних кроку 1

    Returns:
        (is_valid, error_message)
    """
    if not brand or len(brand) < 2:
        return False, "⚠️ Назва бренду повинна містити мінімум 2 символи"

    if not domain:
        return False, "⚠️ Вкажіть домен"

    if not industry:
        return False, "⚠️ Вкажіть галузь"

    if not products or len(products) < 10:
        return False, "⚠️ Опишіть продукти детальніше (мін. 10 символів)"

    return True, ""


def render_step1():
    """Крок 1: Введення даних про бренд"""
    st.subheader("📝 Крок 1: Введіть дані про ваш бренд")

    col1, col2 = st.columns(2)

    with col1:
        brand = st.text_input(
            "Назва бренду *",
            placeholder="Наприклад: Monobank",
            value=st.session_state.get("temp_brand", ""),
            help="Повна назва вашого бренду"
        )

        industry = st.text_input(
            "Галузь / Ніша *",
            placeholder="Наприклад: Фінтех, E-commerce",
            value=st.session_state.get("temp_industry", ""),
            help="Ваша галузь бізнесу"
        )

    with col2:
        domain = st.text_input(
            "Офіційний домен *",
            placeholder="monobank.ua",
            value=st.session_state.get("temp_domain", ""),
            help="Без https://, тільки домен"
        )

        saved_region = st.session_state.get("temp_region", "Ukraine")
        try:
            idx = REGION_OPTIONS.index(saved_region)
        except:
            idx = 0

        region = st.selectbox(
            "Регіон *",
            options=REGION_OPTIONS,
            index=idx,
            help="Основний регіон вашої аудиторії"
        )

    products = st.text_area(
        "Продукти / Послуги *",
        placeholder="Опишіть основні продукти або послуги вашого бренду...",
        value=st.session_state.get("temp_products", ""),
        height=100,
        help="Детальний опис допоможе згенерувати релевантніші запити"
    )

    st.markdown("---")

    col_info, col_button = st.columns([3, 1])

    with col_info:
        st.caption("* - обов'язкові поля")

    with col_button:
        if st.button("🚀 Згенерувати запити", type="primary", use_container_width=True):
            # Валідація
            is_valid, error = validate_step1_data(brand, domain, industry, products)

            if not is_valid:
                st.error(error)
                return

            # Зберігаємо в session state
            st.session_state["temp_brand"] = brand
            st.session_state["temp_domain"] = domain
            st.session_state["temp_industry"] = industry
            st.session_state["temp_products"] = products
            st.session_state["temp_region"] = region

            # Генерація промптів
            with st.spinner("🤖 AI генерує релевантні запити для аналізу..."):
                prompts = n8n_generate_prompts(brand, domain, industry, products)

                if prompts:
                    st.session_state["generated_prompts"] = prompts
                    st.session_state["onboarding_step"] = 2
                    st.success(f"✅ Згенеровано {len(prompts)} запитів!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Помилка генерації. Спробуйте ще раз.")


def render_step2():
    """Крок 2: Перевірка та редагування запитів"""
    st.subheader("✅ Крок 2: Перевірте згенеровані запити")

    prompts_list = st.session_state.get("generated_prompts", [])

    if not prompts_list:
        st.warning("⚠️ Список запитів порожній")
        if st.button("◀ Назад", use_container_width=True):
            st.session_state["onboarding_step"] = 1
            st.rerun()
        return

    st.markdown(f"**AI згенерував {len(prompts_list)} запитів для аналізу**")
    st.caption("Ви можете відредагувати будь-який запит або прибрати галочку, щоб виключити його")

    st.markdown("<br>", unsafe_allow_html=True)

    selected_indices = []

    # Масове редагування
    col_actions = st.columns([1, 1, 2])
    with col_actions[0]:
        if st.button("✅ Вибрати всі", use_container_width=True):
            for i in range(len(prompts_list)):
                st.session_state[f"chk_final_{i}"] = True
            st.rerun()

    with col_actions[1]:
        if st.button("❌ Зняти всі", use_container_width=True):
            for i in range(len(prompts_list)):
                st.session_state[f"chk_final_{i}"] = False
            st.rerun()

    st.markdown("---")

    # Відображення карток з редагуванням
    for i, kw in enumerate(prompts_list):
        edit_key = f"edit_mode_row_{i}"
        checkbox_key = f"chk_final_{i}"

        # Ініціалізація станів
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = True

        with st.container(border=True):
            col_chk, col_num, col_text, col_btn = st.columns([0.5, 0.5, 8, 1])

            # Чекбокс
            with col_chk:
                st.write("")
                is_selected = st.checkbox(
                    "",
                    value=st.session_state[checkbox_key],
                    key=checkbox_key,
                    label_visibility="collapsed"
                )
                if is_selected:
                    selected_indices.append(i)

            # Номер
            with col_num:
                st.markdown(render_green_number(i + 1), unsafe_allow_html=True)

            # Текст або поле вводу
            with col_text:
                if st.session_state[edit_key]:
                    new_val = st.text_input(
                        "",
                        value=kw,
                        key=f"input_kw_{i}",
                        label_visibility="collapsed"
                    )
                else:
                    st.markdown(
                        f"<div style='padding-top: 8px; font-size: 15px;'>{kw}</div>",
                        unsafe_allow_html=True
                    )

            # Кнопка редагування
            with col_btn:
                st.write("")
                if st.session_state[edit_key]:
                    if st.button("💾", key=f"save_kw_{i}", help="Зберегти"):
                        st.session_state["generated_prompts"][i] = new_val
                        st.session_state[edit_key] = False
                        st.rerun()
                else:
                    if st.button("✏️", key=f"edit_kw_{i}", help="Редагувати"):
                        st.session_state[edit_key] = True
                        st.rerun()

    # Підсумок
    final_keywords = [st.session_state["generated_prompts"][idx] 
                     for idx in selected_indices]

    st.markdown("---")

    col_summary, col_actions = st.columns([2, 1])

    with col_summary:
        st.markdown(f"**Обрано:** {len(final_keywords)} з {len(prompts_list)} запитів")
        if len(final_keywords) == 0:
            st.warning("⚠️ Оберіть хоча б один запит")

    with col_actions:
        col_back, col_launch = st.columns(2)

        with col_back:
            if st.button("◀ Назад", use_container_width=True):
                st.session_state["onboarding_step"] = 1
                st.rerun()

        with col_launch:
            if st.button("🎯 Створити проект", type="primary", 
                        use_container_width=True, disabled=len(final_keywords) == 0):
                launch_project(final_keywords)


def launch_project(keywords: List[str]):
    """Створення проекту та запуск аналізу"""
    try:
        user_id = st.session_state["user"].id
        brand_name = st.session_state.get("temp_brand")
        domain_name = st.session_state.get("temp_domain")
        region = st.session_state.get("temp_region", "Ukraine")

        # Прогрес бар
        progress_bar = st.progress(0, text="Створюємо проект...")

        # 1. Створюємо проект (10%)
        project = create_project(user_id, brand_name, domain_name, region, "trial")

        if not project:
            st.error("❌ Помилка створення проекту")
            return

        project_id = project["id"]
        st.session_state["current_project"] = project
        progress_bar.progress(0.1, text="✅ Проект створено")

        # 2. Додаємо домен до whitelist (20%)
        add_official_asset(project_id, domain_name, "website")
        progress_bar.progress(0.2, text="✅ Домен додано")

        # 3. Додаємо ключові слова batch (30%)
        if add_keywords_batch(project_id, keywords):
            progress_bar.progress(0.3, text=f"✅ Додано {len(keywords)} запитів")
        else:
            st.error("❌ Помилка додавання запитів")
            return

        # 4. Запускаємо аналіз (30% -> 100%)
        total_keywords = len(keywords)

        for i, keyword in enumerate(keywords):
            progress = 0.3 + (0.7 * (i + 1) / total_keywords)
            progress_bar.progress(
                progress,
                text=f"🔍 Аналізуємо: {keyword[:30]}..."
            )

            n8n_trigger_analysis(
                project_id=project_id,
                keywords=[keyword],
                brand_name=brand_name,
                models=["Google Gemini"]
            )

            time.sleep(0.3)  # Невелика затримка між запитами

        # Завершення
        progress_bar.progress(1.0, text="🎉 Проект готовий!")
        time.sleep(1)

        # Оновлюємо список проектів
        from database import get_user_projects
        get_user_projects.clear()  # Скидаємо кеш
        st.session_state["projects"] = get_user_projects(user_id)

        # Скидаємо онбординг
        st.session_state["onboarding_step"] = 1
        st.session_state["generated_prompts"] = []

        st.success("✅ Проект успішно створено! Аналіз запущено.")
        st.balloons()

        time.sleep(2)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Критична помилка: {e}")


def render_onboarding():
    """Головна функція рендерингу онбордингу"""
    initialize_onboarding_state()

    st.markdown("## 🚀 Створення нового проекту")

    # Індикатор кроків
    step = st.session_state.get("onboarding_step", 1)

    col_step1, col_step2 = st.columns(2)

    with col_step1:
        status = "✅" if step > 1 else "1️⃣"
        st.markdown(f"### {status} Дані про бренд")

    with col_step2:
        status = "2️⃣" if step == 1 else "✅"
        st.markdown(f"### {status} Запити для аналізу")

    st.markdown("---")

    # Рендеринг відповідного кроку
    with st.container(border=True):
        if step == 1:
            render_step1()
        else:
            render_step2()
