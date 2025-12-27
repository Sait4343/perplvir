"""
Глобальна конфігурація
"""

# N8N webhooks
N8N_GEN_URL = "https://virshi.app.n8n.cloud/webhook/webhook/generate-prompts"
N8N_ANALYZE_URL = "https://virshi.app.n8n.cloud/webhook/webhook/run-analysis_prod"
N8N_RECO_URL = "https://virshi.app.n8n.cloud/webhook/recommendations"
N8N_CHAT_WEBHOOK = "https://virshi.app.n8n.cloud/webhook/webhook/chat-bot"

# Auth header
AUTH_HEADER = {"virshi-auth": "hi@virshi.ai2025"}

# Model mappings
MODEL_MAPPING = {
    "Perplexity": "perplexity",
    "OpenAI GPT": "gpt-4o",
    "Google Gemini": "gemini-1.5-pro"
}

PROVIDER_MAPPING = {
    "perplexity": "Perplexity",
    "gpt-4o": "Chat GPT",
    "gpt-4": "Chat GPT",
    "gemini-1.5-pro": "Gemini",
    "gemini": "Gemini"
}

# Metric tooltips
METRIC_TOOLTIPS = {
    "sov": "Частка видимості вашого бренду у відповідях ШІ порівняно з конкурентами.",
    "official": "Частка посилань на ваші офіційні ресурси.",
    "sentiment": "Тональність: Позитивна, Нейтральна або Негативна.",
    "position": "Середня позиція вашого бренду у списках рекомендацій.",
    "presence": "Відсоток запитів, де бренд був згаданий.",
    "domain": "Відсоток запитів з клікабельним посиланням на ваш домен.",
}

# CSS
CUSTOM_CSS = """
<style>
    .stApp { background-color: #F4F6F9; }

    /* Sidebar */
    section[data-testid="stSidebar"] { 
        background-color: #FFFFFF; 
        border-right: 1px solid #E0E0E0; 
    }

    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Buttons */
    .stButton>button { 
        background-color: #8041F6;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: background-color 0.3s;
    }
    .stButton>button:hover { 
        background-color: #6a35cc;
    }

    /* Green number badge */
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
