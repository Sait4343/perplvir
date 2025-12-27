"""
Переісні UI компоненти
Оптимізація: мінімальний HTML, переіспользування
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional


def render_metric_donut(value: float, color: str = "#00C896", 
                       size: int = 80) -> go.Figure:
    """
    Donut chart для метрик

    Args:
        value: Значення 0-100
        color: Колір заповнення
        size: Розмір графіка

    Returns:
        Plotly Figure
    """
    value = float(value) if value else 0.0
    remaining = max(0, 100 - value)

    fig = go.Figure(
        data=[
            go.Pie(
                values=[value, remaining],
                hole=0.75,
                marker_colors=[color, "#F0F2F6"],
                textinfo="none",
                hoverinfo="label+percent",
            )
        ]
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=size,
        width=size,
        annotations=[
            dict(
                text=f"{int(value)}%",
                x=0.5,
                y=0.5,
                font_size=14,
                showarrow=False,
                font_weight="bold",
                font_color="#333",
            )
        ],
    )

    return fig


def render_status_badge(status: str) -> str:
    """
    HTML бейдж для статусу проекту

    Args:
        status: trial, active, blocked

    Returns:
        HTML string
    """
    badge_map = {
        "trial": ("TRIAL", "#FFECB3", "#856404"),
        "active": ("ACTIVE", "#D4EDDA", "#155724"),
        "blocked": ("BLOCKED", "#F8D7DA", "#721C24"),
    }

    text, bg, color = badge_map.get(status, ("UNKNOWN", "#E0E0E0", "#666"))

    return f'<span style="background-color: {bg}; color: {color}; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.7em;">{text}</span>'


def render_green_number(number: int) -> str:
    """Зелений кружечок з номером"""
    return f'<div class="green-number-small">{number}</div>'


def render_metric_card(label: str, value: str, icon: Optional[str] = None) -> None:
    """Картка метрики"""
    icon_html = f"{icon} " if icon else ""

    html = f"""
    <div class="metric-card-small">
        <div class="metric-label">{icon_html}{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(icon: str, title: str, description: str, 
                      action_text: Optional[str] = None) -> None:
    """Empty state (коли немає даних)"""
    html = f"""
    <div style="text-align: center; padding: 60px 20px; background: white; 
                border-radius: 10px; border: 1px solid #E0E0E0;">
        <div style="font-size: 64px; margin-bottom: 20px;">{icon}</div>
        <h3 style="color: #333; margin-bottom: 10px;">{title}</h3>
        <p style="color: #666; font-size: 14px;">{description}</p>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

    if action_text:
        st.button(action_text, use_container_width=True, type="primary")


def render_sidebar_footer():
    """Футер для сайдбара"""
    st.markdown("---")
    st.caption("Потрібна допомога?")
    st.markdown("📧 [hi@virshi.ai](mailto:hi@virshi.ai)")
    st.caption("© 2025 Virshi AI")
