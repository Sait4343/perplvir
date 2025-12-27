"""
Дашборд: огляд метрик проекту
Оптимізація: lazy loading, кешування агрегацій
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
from database import (
    get_project_keywords, get_scan_results, 
    get_official_assets, db
)
from components import render_metric_donut, render_empty_state
from config import METRIC_TOOLTIPS, MODEL_MAPPING


@st.cache_data(ttl=60, show_spinner=False)
def calculate_metrics(_project_id: str) -> Dict[str, Any]:
    """
    Розрахунок агрегованих метрик
    Кешується на 1 хвилину
    """
    try:
        scans = get_scan_results(_project_id)

        if not scans:
            return {
                "total_scans": 0,
                "sov": 0,
                "presence": 0,
                "official_rate": 0,
                "avg_position": 0,
                "sentiment": {"positive": 0, "neutral": 0, "negative": 0}
            }

        df = pd.DataFrame(scans)

        # Базові метрики
        total_scans = len(df)
        mentioned = df[df['is_brand_mentioned'] == True]
        presence_rate = (len(mentioned) / total_scans * 100) if total_scans > 0 else 0

        # SOV (Share of Voice)
        sov = df['sov_percentage'].mean() if 'sov_percentage' in df.columns else 0

        # Official rate
        official = df[df['has_official_link'] == True]
        official_rate = (len(official) / total_scans * 100) if total_scans > 0 else 0

        # Avg position
        positions = df[df['brand_position'].notna()]['brand_position']
        avg_position = positions.mean() if len(positions) > 0 else 0

        # Sentiment
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        sentiment = {
            "positive": sentiment_counts.get("positive", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "negative": sentiment_counts.get("negative", 0)
        }

        return {
            "total_scans": total_scans,
            "sov": round(sov, 1),
            "presence": round(presence_rate, 1),
            "official_rate": round(official_rate, 1),
            "avg_position": round(avg_position, 1),
            "sentiment": sentiment
        }

    except Exception as e:
        st.error(f"Помилка розрахунку метрик: {e}")
        return {}


def render_kpi_cards(metrics: Dict[str, Any]):
    """Відображення KPI карток"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Share of Voice",
            value=f"{metrics['sov']}%",
            help=METRIC_TOOLTIPS.get("sov", "")
        )

    with col2:
        st.metric(
            label="Присутність",
            value=f"{metrics['presence']}%",
            help=METRIC_TOOLTIPS.get("presence", "")
        )

    with col3:
        st.metric(
            label="Офіційні посилання",
            value=f"{metrics['official_rate']}%",
            help=METRIC_TOOLTIPS.get("official", "")
        )

    with col4:
        if metrics['avg_position'] > 0:
            st.metric(
                label="Середня позиція",
                value=f"#{int(metrics['avg_position'])}",
                help=METRIC_TOOLTIPS.get("position", "")
            )
        else:
            st.metric(label="Середня позиція", value="—")


def render_sentiment_chart(sentiment: Dict[str, int]):
    """Діаграма тональності"""
    total = sum(sentiment.values())

    if total == 0:
        st.info("📊 Недостатньо даних для відображення")
        return

    labels = ["Позитивна", "Нейтральна", "Негативна"]
    values = [sentiment["positive"], sentiment["neutral"], sentiment["negative"]]
    colors = ["#00C896", "#FFC107", "#FF5252"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        hole=0.4,
        textinfo='percent+label',
        textfont_size=14
    )])

    fig.update_layout(
        showlegend=True,
        height=300,
        margin=dict(t=40, b=20, l=20, r=20),
        title=dict(text="Тональність згадок", font_size=16)
    )

    st.plotly_chart(fig, use_container_width=True)


def render_timeline_chart(_project_id: str):
    """Графік динаміки в часі"""
    try:
        scans = get_scan_results(_project_id)

        if not scans or len(scans) < 2:
            st.info("📈 Недостатньо даних для графіка динаміки")
            return

        df = pd.DataFrame(scans)
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date

        # Групування по датам
        daily = df.groupby('date').agg({
            'is_brand_mentioned': 'sum',
            'id': 'count'
        }).reset_index()

        daily.columns = ['date', 'mentions', 'total']
        daily['presence_rate'] = (daily['mentions'] / daily['total'] * 100)

        fig = px.line(
            daily,
            x='date',
            y='presence_rate',
            title='Динаміка присутності бренду',
            labels={'presence_rate': 'Присутність (%)', 'date': 'Дата'}
        )

        fig.update_traces(line_color='#8041F6', line_width=3)
        fig.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20))

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Помилка побудови графіка: {e}")


def render_top_keywords(_project_id: str):
    """Топ-5 запитів за ефективністю"""
    try:
        scans = get_scan_results(_project_id)

        if not scans:
            return

        df = pd.DataFrame(scans)

        # Отримуємо текст ключових слів
        keywords_resp = db.client.table("keywords")\
            .select("id, keyword_text")\
            .eq("project_id", _project_id)\
            .execute()

        kw_map = {k['id']: k['keyword_text'] for k in keywords_resp.data}
        df['keyword_text'] = df['keyword_id'].map(kw_map)

        # Групуємо по ключовому слову
        grouped = df.groupby('keyword_text').agg({
            'is_brand_mentioned': 'sum',
            'id': 'count',
            'sov_percentage': 'mean'
        }).reset_index()

        grouped.columns = ['keyword', 'mentions', 'total', 'avg_sov']
        grouped['presence_rate'] = (grouped['mentions'] / grouped['total'] * 100)
        grouped = grouped.sort_values('avg_sov', ascending=False).head(5)

        st.markdown("### 🏆 Топ-5 запитів за SOV")

        for idx, row in grouped.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{row['keyword']}**")

                with col2:
                    st.metric("SOV", f"{row['avg_sov']:.1f}%")

                with col3:
                    st.metric("Присутність", f"{row['presence_rate']:.0f}%")

    except Exception as e:
        st.error(f"Помилка: {e}")


def render_dashboard():
    """Головна функція дашборду"""
    project = st.session_state.get("current_project")

    if not project:
        render_empty_state(
            icon="📊",
            title="Проект не обрано",
            description="Оберіть проект у сайдбарі або створіть новий"
        )
        return

    # Заголовок
    col_title, col_status = st.columns([3, 1])

    with col_title:
        st.title(f"📊 {project['brand_name']}")
        st.caption(f"Домен: {project['domain']} | Регіон: {project.get('region', 'N/A')}")

    with col_status:
        from components import render_status_badge
        st.markdown(
            render_status_badge(project.get('status', 'trial')),
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Розрахунок метрик
    with st.spinner("Завантаження даних..."):
        metrics = calculate_metrics(project['id'])

    if metrics['total_scans'] == 0:
        render_empty_state(
            icon="🔍",
            title="Немає даних для відображення",
            description="Запустіть перший аналіз, щоб побачити статистику"
        )
        return

    # KPI картки
    render_kpi_cards(metrics)

    st.markdown("---")

    # Графіки
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        render_sentiment_chart(metrics['sentiment'])

    with col_chart2:
        render_timeline_chart(project['id'])

    st.markdown("---")

    # Топ запитів
    render_top_keywords(project['id'])

    # Загальна інформація
    st.markdown("---")
    st.caption(f"Всього сканувань: {metrics['total_scans']} | "
               f"Останнє оновлення: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
