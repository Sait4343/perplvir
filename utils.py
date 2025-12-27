"""
Допоміжні функції
"""

import re
import urllib.parse
import plotly.graph_objects as go
from config import PROVIDER_MAPPING, MODEL_MAPPING

def get_ui_provider(p: str) -> str:
    pstr = str(p).lower()
    for k, v in PROVIDER_MAPPING.items():
        if k in pstr:
            return v
    return str(p).capitalize()

def get_ui_model_name(db_name: str) -> str:
    for ui, db in MODEL_MAPPING.items():
        if db == db_name:
            return ui
    lower = str(db_name).lower()
    if "perplexity" in lower:
        return "Perplexity"
    if "gpt" in lower or "openai" in lower:
        return "OpenAI GPT"
    if "gemini" in lower or "google" in lower:
        return "Google Gemini"
    return db_name

def normalize_url(u: str) -> str:
    u = str(u).strip()
    u = re.split(r"[?#]", u)[0]
    if not u.startswith(("http://", "https://")):
        return f"https://{u}"
    return u

def get_domain(url: str) -> str:
    url = normalize_url(url)
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()

def is_url_official(url: str, whitelist_domains: list) -> bool:
    if not url or not whitelist_domains:
        return False
    try:
        domain = get_domain(url)
        for wl in whitelist_domains:
            wl_clean = str(wl).lower().strip().replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            if wl_clean in domain or domain in wl_clean:
                return True
        return False
    except:
        return False

def get_donut_chart(value, color="#00C896", size=80):
    value = float(value) if value else 0.0
    remaining = max(0, 100 - value)
    fig = go.Figure(data=[go.Pie(values=[value, remaining], hole=0.75, marker_colors=[color, "#F0F2F6"], textinfo="none", hoverinfo="label+percent")])
    fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=size, width=size, annotations=[dict(text=f"{int(value)}%", x=0.5, y=0.5, font_size=14, showarrow=False, font_weight="bold", font_color="#333")])
    return fig
