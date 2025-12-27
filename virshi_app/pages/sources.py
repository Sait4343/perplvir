"""
Сторінка управління офіційними джерелами (whitelist)
Оптимізація: валідація URL, batch додавання
"""

import streamlit as st
import re
from typing import List, Optional
from database import get_official_assets, add_official_asset, db
from components import render_empty_state


def validate_url(url: str) -> tuple[bool, str]:
    """
    Валідація та нормалізація URL

    Returns:
        (is_valid, cleaned_url)
    """
    # Видаляємо пробіли
    url = url.strip()

    # Видаляємо протокол
    url = url.replace("https://", "").replace("http://", "")

    # Видаляємо www
    url = url.replace("www.", "")

    # Видаляємо trailing slash
    url = url.rstrip("/")

    # Базова валідація
    if not url or len(url) < 3:
        return False, ""

    # Перевірка на наявність крапки (домен повинен мати домен верхнього рівня)
    if "." not in url:
        return False, ""

    return True, url


def get_asset_type_icon(asset_type: str) -> str:
    """Іконка для типу ресурсу"""
    icons = {
        "website": "🌐",
        "social": "📱",
        "blog": "📝",
        "shop": "🛒",
        "other": "🔗"
    }
    return icons.get(asset_type, "🔗")


def render_add_asset_form(project_id: str):
    """Форма додавання нового ресурсу"""
    with st.expander("➕ Додати офіційний ресурс", expanded=False):
        with st.form("add_asset_form"):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                url = st.text_input(
                    "URL або домен",
                    placeholder="example.com або facebook.com/yourpage",
                    help="Без https://, просто домен або URL",
                    label_visibility="collapsed"
                )

            with col2:
                asset_type = st.selectbox(
                    "Тип",
                    options=["website", "social", "blog", "shop", "other"],
                    format_func=lambda x: {
                        "website": "🌐 Сайт",
                        "social": "📱 Соцмережі",
                        "blog": "📝 Блог",
                        "shop": "🛒 Магазин",
                        "other": "🔗 Інше"
                    }[x],
                    label_visibility="collapsed"
                )

            with col3:
                submit = st.form_submit_button("Додати", use_container_width=True)

            if submit:
                is_valid, cleaned_url = validate_url(url)

                if not is_valid:
                    st.error("❌ Невірний формат URL")
                else:
                    if add_official_asset(project_id, cleaned_url, asset_type):
                        st.success(f"✅ Додано: {cleaned_url}")
                        st.rerun()
                    else:
                        st.error("❌ Помилка додавання (можливо, вже існує)")


def render_bulk_add_form(project_id: str):
    """Масове додавання ресурсів"""
    with st.expander("📋 Додати кілька ресурсів одразу", expanded=False):
        st.caption("Введіть кожен URL з нового рядка")

        with st.form("bulk_add_form"):
            urls_text = st.text_area(
                "URLs",
                placeholder="example.com\nfacebook.com/page\ntwitter.com/account",
                height=150,
                label_visibility="collapsed"
            )

            col1, col2 = st.columns([3, 1])

            with col1:
                asset_type = st.selectbox(
                    "Тип для всіх",
                    options=["website", "social", "blog", "shop", "other"],
                    format_func=lambda x: {
                        "website": "🌐 Сайт",
                        "social": "📱 Соцмережі",
                        "blog": "📝 Блог",
                        "shop": "🛒 Магазин",
                        "other": "🔗 Інше"
                    }[x]
                )

            with col2:
                submit = st.form_submit_button("Додати всі", use_container_width=True)

            if submit:
                urls = [u.strip() for u in urls_text.split("\n") if u.strip()]

                if not urls:
                    st.warning("⚠️ Введіть хоча б один URL")
                else:
                    added = 0
                    errors = 0

                    progress_bar = st.progress(0)

                    for i, url in enumerate(urls):
                        is_valid, cleaned_url = validate_url(url)

                        if is_valid:
                            if add_official_asset(project_id, cleaned_url, asset_type):
                                added += 1
                            else:
                                errors += 1
                        else:
                            errors += 1

                        progress_bar.progress((i + 1) / len(urls))

                    st.success(f"✅ Додано: {added} | ❌ Помилок: {errors}")
                    st.rerun()


def render_asset_card(asset: dict):
    """Картка одного ресурсу"""
    asset_id = asset['id']
    url = asset['domain_or_url']
    asset_type = asset.get('type', 'other')
    created_at = asset.get('created_at', '')

    icon = get_asset_type_icon(asset_type)

    with st.container(border=True):
        col_icon, col_info, col_actions = st.columns([0.5, 4, 1])

        with col_icon:
            st.markdown(f"<div style='font-size: 32px; margin-top: 10px;'>{icon}</div>", 
                       unsafe_allow_html=True)

        with col_info:
            st.markdown(f"**{url}**")
            st.caption(f"Тип: {asset_type} | Додано: {created_at[:10] if created_at else 'N/A'}")

        with col_actions:
            if st.button("🗑️", key=f"delete_{asset_id}", help="Видалити"):
                st.session_state[f"confirm_delete_{asset_id}"] = True
                st.rerun()

    # Підтвердження видалення
    if st.session_state.get(f"confirm_delete_{asset_id}", False):
        with st.container(border=True):
            st.warning(f"⚠️ Видалити {url}?")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("❌ Скасувати", key=f"cancel_delete_{asset_id}", 
                           use_container_width=True):
                    st.session_state[f"confirm_delete_{asset_id}"] = False
                    st.rerun()

            with col2:
                if st.button("✅ Підтвердити", key=f"confirm_delete_yes_{asset_id}",
                           type="primary", use_container_width=True):
                    try:
                        db.client.table("official_assets")\
                            .delete()\
                            .eq("id", asset_id)\
                            .execute()

                        # Очищаємо кеш
                        from database import get_official_assets
                        get_official_assets.clear()

                        st.success("✅ Видалено!")
                        st.session_state[f"confirm_delete_{asset_id}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Помилка видалення: {e}")


def render_sources_page():
    """Головна функція сторінки джерел"""
    project = st.session_state.get("current_project")

    if not project:
        render_empty_state(
            icon="🔗",
            title="Проект не обрано",
            description="Оберіть проект у сайдбарі"
        )
        return

    st.title("🔗 Офіційні джерела (Whitelist)")

    st.info(
        "💡 **Що це?** Додайте всі офіційні ресурси вашого бренду "
        "(сайт, соцмережі, блог тощо). AI буде відстежувати посилання на них у відповідях."
    )

    # Форми додавання
    render_add_asset_form(project['id'])
    render_bulk_add_form(project['id'])

    st.markdown("---")

    # Завантаження існуючих ресурсів
    assets = get_official_assets(project['id'])

    if not assets:
        render_empty_state(
            icon="🔗",
            title="Немає додаких джерел",
            description="Додайте офіційні ресурси вашого бренду для відстеження"
        )
        return

    # Статистика
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Всього джерел", len(assets))

    with col2:
        websites = len([a for a in assets if a.get('type') == 'website'])
        st.metric("Сайти", websites)

    with col3:
        social = len([a for a in assets if a.get('type') == 'social'])
        st.metric("Соцмережі", social)

    st.markdown("---")

    # Фільтр по типу
    filter_type = st.selectbox(
        "Фільтр по типу",
        options=["all", "website", "social", "blog", "shop", "other"],
        format_func=lambda x: {
            "all": "Всі",
            "website": "🌐 Сайти",
            "social": "📱 Соцмережі",
            "blog": "📝 Блоги",
            "shop": "🛒 Магазини",
            "other": "🔗 Інше"
        }[x]
    )

    # Фільтрація
    if filter_type != "all":
        filtered_assets = [a for a in assets if a.get('type') == filter_type]
    else:
        filtered_assets = assets

    st.markdown(f"**Показано: {len(filtered_assets)}**")
    st.markdown("---")

    # Відображення карток
    for asset in filtered_assets:
        render_asset_card(asset)
