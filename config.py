"""
Конфігурація застосунку
Містить: константи, CSS стилі, маппінги
"""

# =========================
# КОНСТАНТИ
# =========================

# N8N Webhooks (Production)
N8N_GEN_URL = "https://virshi.app.n8n.cloud/webhook/webhook/generate-prompts"
N8N_ANALYZE_URL = "https://virshi.app.n8n.cloud/webhook/webhook/run-analysis_prod"
N8N_RECO_URL = "https://virshi.app.n8n.cloud/webhook/recommendations"
N8N_CHAT_WEBHOOK = "https://virshi.app.n8n.cloud/webhook/webhook/chat-bot"

# Authentication Header
N8N_AUTH_HEADER = {"virshi-auth": "hi@virshi.ai2025"}

# Model Mapping
MODEL_MAPPING = {
    "Perplexity": "perplexity",
    "OpenAI GPT": "gpt-4o",
    "Google Gemini": "gemini-1.5-pro"
}

# Region Options
REGION_OPTIONS = ["Ukraine", "USA", "Europe", "Global"]

# Metric Tooltips
METRIC_TOOLTIPS = {
    "sov": "Частка видимості вашого бренду у відповідях ШІ порівняно з конкурентами.",
    "official": "Частка посилань на ваші офіційні ресурси.",
    "sentiment": "Тональність: Позитивна, Нейтральна або Негативна.",
    "position": "Середня позиція вашого бренду у списках рекомендацій.",
    "presence": "Відсоток запитів, де бренд був згаданий.",
    "domain": "Відсоток запитів з клікабельним посиланням на ваш домен.",
}

# =========================
# CSS СТИЛІ
# =========================

CUSTOM_CSS = """
<style>
    /* 1. ЗАГАЛЬНІ НАЛАШТУВАННЯ */
    .stApp { background-color: #F4F6F9; }

    /* Приховування якірних посилань */
    [data-testid="stMarkdownContainer"] h1 > a,
    [data-testid="stMarkdownContainer"] h2 > a,
    [data-testid="stMarkdownContainer"] h3 > a,
    [data-testid="stMarkdownContainer"] h4 > a,
    [data-testid="stMarkdownContainer"] h5 > a,
    [data-testid="stMarkdownContainer"] h6 > a {
        display: none !important;
    }
    a.anchor-link { display: none !important; }

    /* 2. САЙДБАР */
    section[data-testid="stSidebar"] { 
        background-color: #FFFFFF; 
        border-right: 1px solid #E0E0E0; 
    }
    .sidebar-logo-container { display: flex; justify-content: center; margin-bottom: 10px; }
    .sidebar-logo-container img { width: 140px; }
    .sidebar-name { font-size: 14px; font-weight: 600; color: #333; margin-top: 5px;}
    .sidebar-label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 15px;}

    /* 3. КОНТЕЙНЕРИ І ФОРМИ */
    .css-1r6slb0, .css-12oz5g7, div[data-testid="stForm"] {
        background-color: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #EAEAEA;
    }

    /* 4. МЕТРИКИ */
    div[data-testid="stMetric"] {
        background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px;
        border-radius: 10px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-card-small {
        background-color: #F0F2F6;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 18px; font-weight: bold; color: #8041F6;
    }
    .metric-label {
        font-size: 12px; color: #666;
    }

    /* 5. КНОПКИ */
    .stButton>button { 
        background-color: #8041F6; color: white; border-radius: 8px; border: none; font-weight: 600; 
        transition: background-color 0.3s;
    }
    .stButton>button:hover { background-color: #6a35cc; }

    .upgrade-btn {
        display: block; width: 100%; background-color: #FFC107; color: #000000;
        text-align: center; padding: 8px; border-radius: 8px;
        text-decoration: none; font-weight: bold; margin-top: 10px; border: 1px solid #e0a800;
    }

    /* 6. БЕЙДЖІ ТА СТАТУСИ */
    .badge-trial { background-color: #FFECB3; color: #856404; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.7em; }
    .badge-active { background-color: #D4EDDA; color: #155724; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.7em; }

    /* 7. ВІДПОВІДЬ ШІ */
    .ai-response-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Source Sans Pro', sans-serif;
        line-height: 1.6;
        color: #31333F;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        max-height: 600px;
        overflow-y: auto;
    }

    /* 8. ЗЕЛЕНІ НОМЕРИ */
    .green-number-small {
        background-color: #00C896;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
        margin-top: 8px;
    }
</style>
"""
