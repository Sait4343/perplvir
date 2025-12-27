"""
Головна сторінка дашборда
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from database import db, get_scan_results, get_project_keywords
from components import render_metric_donut, render_status_badge

def calculate_metrics(scan_results, brand_name: str):
    if not scan_results:
        return {"sov": 0, "official": 0, "sentiment": "N/A", "position": 0, "presence": 0, "domain": 0}

    total_scans = len(scan_results)
    brand_mentions = sum(1 for s in scan_results if brand_name.lower() in str(s.get("mentioned_brands", "")).lower())
    official_links = sum(1 for s in scan_results if s.get("links_to_official_site", False))

    sentiments = [s.get("sentiment", "neutral") for s in scan_results]
    sentiment_counts = pd.Series(sentiments).value_counts().to_dict()
    dominant_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"

    positions = [s.get("brand_position") for s in scan_results if s.get("brand_position")]
    avg_position = round(sum(positions) / len(positions), 1) if positions else 0

    return {
        "sov": round((brand_mentions / total_scans) * 100, 1) if total_scans else 0,
        "official": round((official_links / total_scans) * 100, 1) if total_scans else 0,
        "sentiment": dominant_sentiment.capitalize(),
        "position": avg_position,
        "presence": round((brand_mentions / total_scans) * 100, 1) if total_scans else 0,
        "domain": round((official_links / total_scans) * 100, 1) if total_scans else 0
    }

def render_dashboard():
    st.title("🚀 Дашборд")

    project = st.session_state.get("current_project")
    if not project:
        st.info("Створіть проект для початку роботи")
        return

    brand_name = project.get("brand_name", "Brand")
    status = project.get("status", "trial")

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {brand_name}")
        st.markdown(f"**Домен:** {project.get('domain', 'N/A')} | **Регіон:** {project.get('region', 'Ukraine')}")
    with col2:
        st.markdown(render_status_badge(status), unsafe_allow_html=True)

    st.divider()

    # Metrics
    scan_results = get_scan_results(project["id"])
    metrics = calculate_metrics(scan_results, brand_name)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Share of Voice**")
        st.plotly_chart(render_metric_donut(metrics["sov"], "#8041F6"), use_container_width=True)

    with col2:
        st.markdown("**Official Links**")
        st.plotly_chart(render_metric_donut(metrics["official"], "#00C896"), use_container_width=True)

    with col3:
        st.markdown("**Sentiment**")
        sentiment_color = {"positive": "#00C896", "neutral": "#FFC107", "negative": "#FF5252"}.get(metrics["sentiment"].lower(), "#999")
        st.markdown(f'<div style="text-align: center; padding: 20px;"><span style="font-size: 24px; color: {sentiment_color}; font-weight: bold;">{metrics["sentiment"]}</span></div>', unsafe_allow_html=True)

    with col4:
        st.markdown("**Avg Position**")
        st.markdown(f'<div style="text-align: center; padding: 20px;"><span style="font-size: 32px; color: #333; font-weight: bold;">{metrics["position"]}</span></div>', unsafe_allow_html=True)

    st.divider()

    # Keywords table
    st.markdown("### 📝 Останні запити")
    keywords = get_project_keywords(project["id"])

    if keywords:
        df = pd.DataFrame(keywords)
        df = df[["keyword_text", "created_at"]].head(10)
        df.columns = ["Запит", "Створено"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Запити ще не створені")
