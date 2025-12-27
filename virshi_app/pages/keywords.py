"""
Сторінка управління ключовими словами
Оптимізація: пагінація, batch операції, фільтрація
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Optional
from database import (
    get_project_keywords, add_keyword, update_keyword_status,
    get_scan_results, db
)
from n8n.webhooks import n8n_trigger_analysis
from components import render_empty_state
from config import MODEL_MAPPING


# Константи
ITEMS_PER_PAGE = 20


def initialize_keywords_state():
    """Ініціалізація стану сторінки"""
    if "kw_page" not in st.session_state:
        st.session_state["kw_page"] = 1
    if "kw_filter" not in st.session_state:
        st.session_state["kw_filter"] = "all"
    if "kw_search" not in st.session_state:
        st.session_state["kw_search"] = ""


def get_filtered_keywords(project_id: str, filter_type: str, 
                          search_query: str) -> List[dict]:
    """Отримання відфільтрованих ключових слів"""
    # Отримуємо всі keywords
    all_keywords = get_project_keywords(project_id, active_only=False)

    # Фільтр по статусу
    if filter_type == "active":
        all_keywords = [kw for kw in all_keywords if kw.get('is_active', True)]
    elif filter_type == "inactive":
        all_keywords = [kw for kw in all_keywords if not kw.get('is_active', True)]

    # Пошук
    if search_query:
        all_keywords = [
            kw for kw in all_keywords 
            if search_query.lower() in kw['keyword_text'].lower()
        ]

    return all_keywords


def get_keyword_stats(keyword_id: str) -> dict:
    """Отримання статистики по ключовому слову"""
    try:
        scans_resp = db.client.table("scan_results")\
            .select("*")\
            .eq("keyword_id", keyword_id)\
            .execute()

        scans = scans_resp.data or []

        if not scans:
            return {"total": 0, "mentioned": 0, "sov": 0}

        df = pd.DataFrame(scans)
        mentioned = df[df['is_brand_mentioned'] == True]

        return {
            "total": len(df),
            "mentioned": len(mentioned),
            "sov": round(df['sov_percentage'].mean(), 1) if 'sov_percentage' in df.columns else 0
        }
    except:
        return {"total": 0, "mentioned": 0, "sov": 0}


def render_add_keyword_form(project_id: str):
    """Форма додавання нового ключового слова"""
    with st.expander("➕ Додати нове ключове слово", expanded=False):
        with st.form("add_keyword_form"):
            col1, col2 = st.columns([3, 1])

            with col1:
                new_keyword = st.text_input(
                    "Ключове слово",
                    placeholder="Наприклад: найкращий банк для бізнесу",
                    label_visibility="collapsed"
                )

            with col2:
                submit = st.form_submit_button("Додати", use_container_width=True)

            if submit:
                if new_keyword and len(new_keyword) >= 3:
                    if add_keyword(project_id, new_keyword, is_active=True):
                        st.success("✅ Ключове слово додано!")
                        st.rerun()
                    else:
                        st.error("❌ Помилка додавання")
                else:
                    st.warning("⚠️ Введіть мінімум 3 символи")


def render_keyword_row(keyword: dict, index: int):
    """Рендер одного рядка з ключовим словом"""
    kw_id = keyword['id']
    kw_text = keyword['keyword_text']
    is_active = keyword.get('is_active', True)

    # Отримуємо статистику
    stats = get_keyword_stats(kw_id)

    with st.container(border=True):
        col_check, col_text, col_stats, col_actions = st.columns([0.5, 4, 2, 1.5])

        # Чекбокс для вибору
        with col_check:
            st.write("")
            selected = st.checkbox(
                "",
                key=f"select_kw_{kw_id}",
                label_visibility="collapsed"
            )

        # Текст ключового слова
        with col_text:
            status_icon = "✅" if is_active else "⏸️"
            st.markdown(f"{status_icon} **{kw_text}**")
            st.caption(f"ID: {kw_id[:8]}...")

        # Статистика
        with col_stats:
            if stats['total'] > 0:
                st.metric("Сканувань", stats['total'])
                st.caption(f"SOV: {stats['sov']}%")
            else:
                st.caption("Немає даних")

        # Дії
        with col_actions:
            col_toggle, col_scan = st.columns(2)

            with col_toggle:
                if is_active:
                    if st.button("⏸️", key=f"pause_{kw_id}", help="Деактивувати"):
                        update_keyword_status(kw_id, False)
                        st.rerun()
                else:
                    if st.button("▶️", key=f"play_{kw_id}", help="Активувати"):
                        update_keyword_status(kw_id, True)
                        st.rerun()

            with col_scan:
                if st.button("🔍", key=f"scan_{kw_id}", help="Сканувати"):
                    st.session_state[f"scan_modal_{kw_id}"] = True
                    st.rerun()

    # Модальне вікно для сканування
    if st.session_state.get(f"scan_modal_{kw_id}", False):
        render_scan_modal(kw_id, kw_text)


def render_scan_modal(kw_id: str, kw_text: str):
    """Модальне вікно для запуску сканування"""
    project = st.session_state.get("current_project")

    with st.container(border=True):
        st.markdown(f"### 🔍 Сканування: {kw_text}")

        # Вибір моделі
        model = st.selectbox(
            "Оберіть модель AI",
            options=list(MODEL_MAPPING.keys()),
            key=f"model_select_{kw_id}"
        )

        col_cancel, col_start = st.columns(2)

        with col_cancel:
            if st.button("❌ Скасувати", key=f"cancel_scan_{kw_id}", use_container_width=True):
                st.session_state[f"scan_modal_{kw_id}"] = False
                st.rerun()

        with col_start:
            if st.button("🚀 Запустити", key=f"start_scan_{kw_id}", 
                        type="primary", use_container_width=True):
                with st.spinner(f"Аналізуємо: {kw_text}..."):
                    success = n8n_trigger_analysis(
                        project_id=project['id'],
                        keywords=[kw_text],
                        brand_name=project['brand_name'],
                        models=[model]
                    )

                    if success:
                        st.success("✅ Аналіз запущено!")
                        st.session_state[f"scan_modal_{kw_id}"] = False
                        st.rerun()
                    else:
                        st.error("❌ Помилка запуску")


def render_bulk_actions(selected_keywords: List[str], project: dict):
    """Масові дії над обраними ключовими словами"""
    if not selected_keywords:
        return

    st.markdown(f"**Обрано: {len(selected_keywords)} ключових слів**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Активувати всі", use_container_width=True):
            for kw_id in selected_keywords:
                update_keyword_status(kw_id, True)
            st.success("✅ Активовано!")
            st.rerun()

    with col2:
        if st.button("⏸️ Деактивувати всі", use_container_width=True):
            for kw_id in selected_keywords:
                update_keyword_status(kw_id, False)
            st.success("✅ Деактивовано!")
            st.rerun()

    with col3:
        if st.button("🔍 Сканувати всі", use_container_width=True):
            st.session_state["bulk_scan_modal"] = True
            st.rerun()


def render_keywords_page():
    """Головна функція сторінки ключових слів"""
    initialize_keywords_state()

    project = st.session_state.get("current_project")

    if not project:
        render_empty_state(
            icon="📝",
            title="Проект не обрано",
            description="Оберіть проект у сайдбарі"
        )
        return

    st.title("📝 Управління ключовими словами")

    # Форма додавання
    render_add_keyword_form(project['id'])

    st.markdown("---")

    # Фільтри та пошук
    col_filter, col_search = st.columns([1, 2])

    with col_filter:
        filter_type = st.selectbox(
            "Фільтр",
            options=[("all", "Всі"), ("active", "Активні"), ("inactive", "Неактивні")],
            format_func=lambda x: x[1],
            key="filter_select"
        )[0]
        st.session_state["kw_filter"] = filter_type

    with col_search:
        search_query = st.text_input(
            "🔍 Пошук",
            placeholder="Введіть текст для пошуку...",
            key="search_input"
        )
        st.session_state["kw_search"] = search_query

    # Отримуємо відфільтровані keywords
    filtered_keywords = get_filtered_keywords(
        project['id'],
        st.session_state["kw_filter"],
        st.session_state["kw_search"]
    )

    total_keywords = len(filtered_keywords)

    if total_keywords == 0:
        render_empty_state(
            icon="🔍",
            title="Ключових слів не знайдено",
            description="Додайте нові ключові слова або змініть фільтри"
        )
        return

    # Пагінація
    total_pages = (total_keywords + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    current_page = st.session_state.get("kw_page", 1)

    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_keywords)

    page_keywords = filtered_keywords[start_idx:end_idx]

    # Інформація про результати
    st.markdown(f"**Показано {start_idx + 1}-{end_idx} з {total_keywords}**")

    st.markdown("---")

    # Відображення ключових слів
    for idx, keyword in enumerate(page_keywords):
        render_keyword_row(keyword, start_idx + idx)

    # Пагінація (навігація)
    if total_pages > 1:
        st.markdown("---")
        col_prev, col_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button("◀ Попередня", disabled=current_page == 1, use_container_width=True):
                st.session_state["kw_page"] = current_page - 1
                st.rerun()

        with col_info:
            st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Сторінка {current_page} з {total_pages}</div>", 
                       unsafe_allow_html=True)

        with col_next:
            if st.button("Наступна ▶", disabled=current_page == total_pages, use_container_width=True):
                st.session_state["kw_page"] = current_page + 1
                st.rerun()
