"""
Модуль N8N Webhooks
Оптимізація: timeout handling, retry logic
"""

import requests
import streamlit as st
from typing import List, Optional, Dict, Any
from datetime import datetime
from config import (
    N8N_GEN_URL, N8N_ANALYZE_URL, N8N_RECO_URL, 
    N8N_CHAT_WEBHOOK, N8N_AUTH_HEADER, MODEL_MAPPING
)
from database import db, check_keyword_scanned


def n8n_generate_prompts(brand: str, domain: str, industry: str, 
                         products: str, timeout: int = 60) -> List[str]:
    """
    Генерація промптів через N8N

    Args:
        brand: Назва бренду
        domain: Домен
        industry: Галузь
        products: Продукти/послуги
        timeout: Таймаут в секундах

    Returns:
        Список згенерованих промптів
    """
    try:
        payload = {
            "brand": brand,
            "domain": domain,
            "industry": industry,
            "products": products,
        }

        response = requests.post(
            N8N_GEN_URL, 
            json=payload, 
            headers=N8N_AUTH_HEADER, 
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()

            # Обробка різних форматів відповіді
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("prompts", [])
            else:
                return []
        else:
            st.error(f"❌ N8N Error: {response.status_code} - {response.text}")
            return []

    except requests.exceptions.Timeout:
        st.error("⏱️ Час очікування вичерпано. Спробуйте ще раз.")
        return []
    except Exception as e:
        st.error(f"❌ Помилка з'єднання з N8N: {e}")
        return []


def n8n_trigger_analysis(project_id: str, keywords: List[str], 
                        brand_name: str, models: Optional[List[str]] = None,
                        timeout: int = 60) -> bool:
    """
    Запуск аналізу через N8N

    TRIAL LOGIC:
    - Trial дозволяє сканувати будь-яку модель
    - Trial дозволяє сканувати конкретний запит лише 1 раз

    Args:
        project_id: ID проекту
        keywords: Список ключових слів
        brand_name: Назва бренду
        models: Список моделей для аналізу
        timeout: Таймаут

    Returns:
        True якщо успішно, False якщо помилка
    """

    # Отримуємо статус проекту
    current_proj = st.session_state.get("current_project", {})
    status = current_proj.get("status", "trial")

    if status == "blocked":
        st.error("⛔ Проект заблоковано. Зверніться до адміністратора.")
        return False

    if not models:
        models = ["Perplexity"]

    # Нормалізація keywords
    if isinstance(keywords, str):
        keywords_list = [keywords]
    else:
        keywords_list = keywords

    # === TRIAL LOGIC ===
    if status == "trial":
        try:
            # Отримуємо ID ключових слів
            kw_resp = db.client.table("keywords")\
                .select("id, keyword_text")\
                .eq("project_id", project_id)\
                .in_("keyword_text", keywords_list)\
                .execute()

            kw_map = {item['keyword_text']: item['id'] 
                     for item in kw_resp.data} if kw_resp.data else {}

            allowed_keywords = []
            blocked_keywords = []

            for kw_text in keywords_list:
                kw_id = kw_map.get(kw_text)

                if kw_id:
                    # Перевіряємо чи вже сканували
                    if check_keyword_scanned(kw_id):
                        blocked_keywords.append(kw_text)
                    else:
                        allowed_keywords.append(kw_text)
                else:
                    # Нове слово - дозволяємо
                    allowed_keywords.append(kw_text)

            if blocked_keywords:
                st.warning(
                    f"🔒 Наступні запити вже були проскановані (Trial ліміт 1 раз): "
                    f"{', '.join(blocked_keywords[:3])}..."
                )

            if not allowed_keywords:
                st.error("⛔ Всі обрані запити вже були проскановані.")
                return False

            # Оновлюємо список
            keywords_list = allowed_keywords

        except Exception as e:
            st.warning(f"⚠️ Не вдалося перевірити ліміти Trial: {e}")
            return False

    # === ОТРИМАННЯ WHITELIST ===
    clean_assets = []
    try:
        assets_resp = db.client.table("official_assets")\
            .select("domain_or_url")\
            .eq("project_id", project_id)\
            .execute()

        if assets_resp.data:
            for item in assets_resp.data:
                raw_url = item.get("domain_or_url", "").lower().strip()
                clean = raw_url.replace("https://", "")\
                    .replace("http://", "")\
                    .replace("www.", "")\
                    .rstrip("/")
                if clean:
                    clean_assets.append(clean)
    except Exception as e:
        print(f"Error fetching assets: {e}")

    # === ВІДПРАВКА ===
    try:
        user = st.session_state.get("user")
        user_email = user.email if user else "no-reply@virshi.ai"
        success_count = 0

        for ui_model_name in models:
            tech_model_id = MODEL_MAPPING.get(ui_model_name, ui_model_name)

            payload = {
                "project_id": project_id,
                "keywords": keywords_list,
                "brand_name": brand_name,
                "user_email": user_email,
                "provider": tech_model_id,
                "models": [tech_model_id],
                "official_assets": clean_assets
            }

            try:
                response = requests.post(
                    N8N_ANALYZE_URL,
                    json=payload,
                    headers=N8N_AUTH_HEADER,
                    timeout=timeout
                )

                if response.status_code == 200:
                    success_count += 1
                else:
                    st.error(f"❌ Помилка n8n ({ui_model_name}): {response.text}")

            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout для {ui_model_name}")
            except Exception as inner_e:
                st.error(f"❌ Не вдалося запустити {ui_model_name}: {inner_e}")

        return success_count > 0

    except Exception as e:
        st.error(f"❌ Критична помилка запуску: {e}")
        return False


def trigger_ai_recommendation(user, project: Dict[str, Any], 
                              category: str, context_text: str,
                              timeout: int = 120) -> str:
    """
    Генерація AI рекомендацій (HTML звіт)

    Args:
        user: Об'єкт користувача
        project: Дані проекту
        category: Категорія рекомендації
        context_text: Контекст запиту
        timeout: Таймаут

    Returns:
        HTML звіт або помилка
    """
    payload = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user.id if user else "unknown",
        "user_email": user.email if user else "unknown",
        "project_id": project.get("id"),
        "brand_name": project.get("brand_name"),
        "domain": project.get("domain"),
        "category": category,
        "request_context": context_text,
        "request_type": "html_report"
    }

    try:
        response = requests.post(
            N8N_RECO_URL, 
            json=payload, 
            headers=N8N_AUTH_HEADER, 
            timeout=timeout
        )

        if response.status_code == 200:
            try:
                data = response.json()
                return data.get("html") or data.get("output") or \
                       data.get("report") or str(data)
            except:
                return response.text
        else:
            return f"<p style='color:red; font-weight:bold;'>"                   f"Error from AI Provider: {response.status_code}</p>"

    except requests.exceptions.Timeout:
        return "<p style='color:red; font-weight:bold;'>⏱️ Час очікування вичерпано</p>"
    except Exception as e:
        return f"<p style='color:red; font-weight:bold;'>Connection Error: {e}</p>"


def n8n_chat_request(message: str, context: Optional[Dict] = None,
                     timeout: int = 60) -> str:
    """
    Відправка запиту до чат-бота

    Args:
        message: Повідомлення користувача
        context: Додатковий контекст
        timeout: Таймаут

    Returns:
        Відповідь від бота
    """
    payload = {
        "message": message,
        "context": context or {},
        "timestamp": datetime.now().isoformat()
    }

    try:
        response = requests.post(
            N8N_CHAT_WEBHOOK,
            json=payload,
            headers=N8N_AUTH_HEADER,
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "Помилка обробки відповіді")
        else:
            return f"Помилка: {response.status_code}"

    except Exception as e:
        return f"Помилка з'єднання: {e}"
