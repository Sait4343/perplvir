"""
Competitors analysis page
"""

import streamlit as st
import pandas as pd
from database import get_scan_results

def render_competitors_page():
    st.title("👥 Конкуренти")

    project = st.session_state.get("current_project")
    if not project:
        st.info("Створіть проект")
        return

    scan_results = get_scan_results(project["id"])

    if not scan_results:
        st.info("Дані відсутні. Запустіть аналіз запитів.")
        return

    # Extract competitors
    all_brands = []
    for scan in scan_results:
        brands_str = scan.get("mentioned_brands", "")
        if brands_str:
            brands = [b.strip() for b in str(brands_str).split(",")]
            all_brands.extend(brands)

    if not all_brands:
        st.info("Конкуренти не виявлені")
        return

    # Count frequency
    df = pd.DataFrame({"Brand": all_brands})
    freq = df["Brand"].value_counts().reset_index()
    freq.columns = ["Бренд", "Згадувань"]

    st.markdown("### 📊 Топ конкурентів за згадуваннями")
    st.dataframe(freq.head(20), use_container_width=True, hide_index=True)
