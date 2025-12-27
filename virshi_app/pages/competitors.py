"""
Сторінка аналізу конкурентів
Оптимізація: агрегація даних, кешування, візуалізації
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any
from database import get_competitors, get_scan_results, db
from components import render_empty_state


@st.cache_data(ttl=120, show_spinner=False)
def analyze_competitors(_project_id: str, official_brand: str) -> pd.DataFrame:
    """
    Аналіз конкурентів з агрегацією даних
    Кешується на 2 хвилини
    """
    try:
        scans = get_scan_results(_project_id)

        if not scans:
            return pd.DataFrame()

        # Збираємо всі згадки брендів
        all_brands = []

        for scan in scans:
            mentions = scan.get('brand_mentions', [])

            if isinstance(mentions, list):
                for brand in mentions:
                    all_brands.append({
                        'brand': brand,
                        'scan_id': scan['id'],
                        'keyword_id': scan['keyword_id'],
                        'is_official': brand.lower() == official_brand.lower()
                    })

        if not all_brands:
            return pd.DataFrame()

        df = pd.DataFrame(all_brands)

        # Агрегація
        summary = df.groupby('brand').agg({
            'scan_id': 'count',
            'is_official': 'first'
        }).reset_index()

        summary.columns = ['brand', 'mentions', 'is_official']
        summary = summary.sort_values('mentions', ascending=False)

        return summary

    except Exception as e:
        st.error(f"Помилка аналізу: {e}")
        return pd.DataFrame()


def render_competitors_chart(df: pd.DataFrame):
    """Графік топ-10 конкурентів"""
    if df.empty or len(df) == 0:
        st.info("📊 Недостатньо даних для графіка")
        return

    top10 = df.head(10)

    # Колір: зелений для офіційного бренду, сірий для інших
    colors = ['#00C896' if is_off else '#E0E0E0' 
              for is_off in top10['is_official']]

    fig = go.Figure([go.Bar(
        x=top10['mentions'],
        y=top10['brand'],
        orientation='h',
        marker_color=colors,
        text=top10['mentions'],
        textposition='outside'
    )])

    fig.update_layout(
        title='Топ-10 брендів за кількістю згадок',
        xaxis_title='Кількість згадок',
        yaxis_title='Бренд',
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_add_competitor_form(project_id: str):
    """Форма додавання конкурента"""
    with st.expander("➕ Додати конкурента вручну", expanded=False):
        st.caption("Додайте конкурента для відстеження в майбутніх аналізах")

        with st.form("add_competitor_form"):
            col1, col2 = st.columns([3, 1])

            with col1:
                competitor_name = st.text_input(
                    "Назва конкурента",
                    placeholder="Наприклад: PrivatBank",
                    label_visibility="collapsed"
                )

            with col2:
                submit = st.form_submit_button("Додати", use_container_width=True)

            if submit:
                if competitor_name and len(competitor_name) >= 2:
                    try:
                        db.client.table("competitors").insert({
                            "project_id": project_id,
                            "competitor_name": competitor_name,
                            "is_active": True
                        }).execute()

                        # Очищаємо кеш
                        from database import get_competitors
                        get_competitors.clear()

                        st.success(f"✅ Додано: {competitor_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Помилка: {e}")
                else:
                    st.warning("⚠️ Введіть назву (мін. 2 символи)")


def render_competitors_table(df: pd.DataFrame):
    """Таблиця конкурентів"""
    if df.empty:
        return

    st.markdown("### 📋 Детальна статистика")

    # Додаємо відносну частку
    total_mentions = df['mentions'].sum()
    df['share'] = (df['mentions'] / total_mentions * 100).round(1)

    # Форматуємо для відображення
    display_df = df[['brand', 'mentions', 'share']].copy()
    display_df.columns = ['Бренд', 'Згадки', 'Частка (%)']

    # Додаємо іконку для офіційного бренду
    display_df['Бренд'] = display_df.apply(
        lambda row: f"✅ {row['Бренд']}" if df.iloc[row.name]['is_official'] 
        else row['Бренд'],
        axis=1
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )


def render_competitors_page():
    """Головна функція сторінки конкурентів"""
    project = st.session_state.get("current_project")

    if not project:
        render_empty_state(
            icon="👥",
            title="Проект не обрано",
            description="Оберіть проект у сайдбарі"
        )
        return

    st.title("👥 Аналіз конкурентів")

    st.info(
        "💡 **Як це працює:** AI автоматично виявляє всі бренди, "
        "згадані у відповідях, та показує їх частку видимості."
    )

    # Форма додавання
    render_add_competitor_form(project['id'])

    st.markdown("---")

    # Аналіз
    with st.spinner("Аналізуємо конкурентів..."):
        df = analyze_competitors(project['id'], project['brand_name'])

    if df.empty:
        render_empty_state(
            icon="🔍",
            title="Немає даних",
            description="Запустіть аналіз, щоб побачити конкурентів"
        )
        return

    # Метрики
    col1, col2, col3 = st.columns(3)

    official_row = df[df['is_official'] == True]

    with col1:
        st.metric("Всього брендів", len(df))

    with col2:
        if not official_row.empty:
            official_mentions = official_row.iloc[0]['mentions']
            st.metric("Згадки вашого бренду", official_mentions)
        else:
            st.metric("Згадки вашого бренду", 0)

    with col3:
        if not official_row.empty:
            total = df['mentions'].sum()
            sov = (official_row.iloc[0]['mentions'] / total * 100) if total > 0 else 0
            st.metric("Share of Voice", f"{sov:.1f}%")
        else:
            st.metric("Share of Voice", "0%")

    st.markdown("---")

    # Графік
    render_competitors_chart(df)

    st.markdown("---")

    # Таблиця
    render_competitors_table(df)

    # Список відстежуваних конкурентів
    st.markdown("---")
    st.markdown("### 🎯 Відстежувані конкуренти")

    tracked = get_competitors(project['id'])

    if tracked:
        for competitor in tracked:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**{competitor['competitor_name']}**")

                with col2:
                    if st.button("🗑️", key=f"del_comp_{competitor['id']}", 
                               help="Видалити"):
                        try:
                            db.client.table("competitors")\
                                .delete()\
                                .eq("id", competitor['id'])\
                                .execute()

                            from database import get_competitors
                            get_competitors.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")
    else:
        st.caption("Немає відстежуваних конкурентів")
