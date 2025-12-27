"""
Модуль роботи з базою даних
Оптимізація: кешування, lazy loading, ефективні запити
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class Database:
    """Singleton клас для роботи з Supabase"""

    _instance = None
    _client: Optional[Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def initialize(self, url: str, key: str):
        """Ініціалізація підключення"""
        if self._client is None:
            self._client = create_client(url, key)
        return self._client

    @property
    def client(self) -> Client:
        """Getter для клієнта"""
        if self._client is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._client


# Глобальний екземпляр
db = Database()


# =========================
# КЕШОВАНІ ЗАПИТИ
# =========================

@st.cache_data(ttl=300, show_spinner=False)  # Кеш на 5 хвилин
def get_user_projects(_user_id: str) -> List[Dict[str, Any]]:
    """Отримати всі проекти користувача"""
    try:
        response = db.client.table("projects")\
            .select("*")\
            .eq("user_id", _user_id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data or []
    except Exception as e:
        st.error(f"Помилка завантаження проектів: {e}")
        return []


@st.cache_data(ttl=60, show_spinner=False)  # Кеш на 1 хвилину
def get_project_keywords(_project_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """Отримати ключові слова проекту"""
    try:
        query = db.client.table("keywords")\
            .select("*")\
            .eq("project_id", _project_id)

        if active_only:
            query = query.eq("is_active", True)

        response = query.order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Помилка завантаження ключових слів: {e}")
        return []


@st.cache_data(ttl=60, show_spinner=False)
def get_scan_results(_project_id: str, _keyword_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Отримати результати сканувань"""
    try:
        query = db.client.table("scan_results")\
            .select("*")\
            .eq("project_id", _project_id)

        if _keyword_id:
            query = query.eq("keyword_id", _keyword_id)

        response = query.order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Помилка завантаження результатів: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def get_official_assets(_project_id: str) -> List[Dict[str, Any]]:
    """Отримати офіційні ресурси проекту"""
    try:
        response = db.client.table("official_assets")\
            .select("*")\
            .eq("project_id", _project_id)\
            .execute()
        return response.data or []
    except Exception as e:
        st.error(f"Помилка завантаження ресурсів: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def get_competitors(_project_id: str) -> List[Dict[str, Any]]:
    """Отримати конкурентів проекту"""
    try:
        response = db.client.table("competitors")\
            .select("*")\
            .eq("project_id", _project_id)\
            .eq("is_active", True)\
            .execute()
        return response.data or []
    except Exception as e:
        st.error(f"Помилка завантаження конкурентів: {e}")
        return []


# =========================
# ЗАПИТИ БЕЗ КЕШУВАННЯ (WRITE)
# =========================

def create_project(user_id: str, brand_name: str, domain: str, 
                   region: str = "Ukraine", status: str = "trial") -> Optional[Dict[str, Any]]:
    """Створити новий проект"""
    try:
        response = db.client.table("projects").insert({
            "user_id": user_id,
            "brand_name": brand_name,
            "domain": domain,
            "region": region,
            "status": status
        }).execute()

        # Скидаємо кеш
        get_user_projects.clear()

        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Помилка створення проекту: {e}")
        return None


def add_keyword(project_id: str, keyword_text: str, is_active: bool = True) -> bool:
    """Додати ключове слово"""
    try:
        db.client.table("keywords").insert({
            "project_id": project_id,
            "keyword_text": keyword_text,
            "is_active": is_active
        }).execute()

        # Скидаємо кеш
        get_project_keywords.clear()
        return True
    except Exception as e:
        st.error(f"Помилка додавання ключового слова: {e}")
        return False


def add_keywords_batch(project_id: str, keywords: List[str]) -> bool:
    """Додати кілька ключових слів одразу (batch insert)"""
    try:
        data = [{"project_id": project_id, "keyword_text": kw, "is_active": True} 
                for kw in keywords]
        db.client.table("keywords").insert(data).execute()

        get_project_keywords.clear()
        return True
    except Exception as e:
        st.error(f"Помилка batch додавання: {e}")
        return False


def update_keyword_status(keyword_id: str, is_active: bool) -> bool:
    """Оновити статус ключового слова"""
    try:
        db.client.table("keywords")\
            .update({"is_active": is_active})\
            .eq("id", keyword_id)\
            .execute()

        get_project_keywords.clear()
        return True
    except Exception as e:
        st.error(f"Помилка оновлення статусу: {e}")
        return False


def add_official_asset(project_id: str, domain_or_url: str, 
                       asset_type: str = "website") -> bool:
    """Додати офіційний ресурс"""
    try:
        # Очищаємо домен
        clean_url = domain_or_url.replace("https://", "").replace("http://", "")\
            .replace("www.", "").strip().rstrip("/")

        db.client.table("official_assets").insert({
            "project_id": project_id,
            "domain_or_url": clean_url,
            "type": asset_type
        }).execute()

        get_official_assets.clear()
        return True
    except Exception as e:
        st.error(f"Помилка додавання ресурсу: {e}")
        return False


def check_keyword_scanned(keyword_id: str) -> bool:
    """Перевірити чи було слово вже проскановано (для trial)"""
    try:
        response = db.client.table("scan_results")\
            .select("id", count="exact")\
            .eq("keyword_id", keyword_id)\
            .limit(1)\
            .execute()

        return response.count > 0 if response.count else False
    except:
        return False


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Отримати профіль користувача"""
    try:
        response = db.client.table("profiles")\
            .select("*")\
            .eq("id", user_id)\
            .single()\
            .execute()
        return response.data
    except:
        return None


def create_user_profile(user_id: str, email: str, first_name: str, 
                       last_name: str, role: str = "user") -> bool:
    """Створити профіль користувача"""
    try:
        db.client.table("profiles").insert({
            "id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role
        }).execute()
        return True
    except:
        return False


# =========================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================

def clear_all_caches():
    """Очистити всі кеші (використовувати після logout)"""
    get_user_projects.clear()
    get_project_keywords.clear()
    get_scan_results.clear()
    get_official_assets.clear()
    get_competitors.clear()
