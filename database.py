"""
Supabase database manager
"""

import streamlit as st
from supabase import create_client, Client
from typing import Dict, Any, List, Optional
from functools import lru_cache

class DatabaseManager:
    def __init__(self):
        try:
            self.url: str = st.secrets["SUPABASE_URL"]
            self.key: str = st.secrets["SUPABASE_KEY"]
            self.client: Client = create_client(self.url, self.key)
            self.connected = True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            self.connected = False
            st.stop()

db = DatabaseManager()

# USER PROFILE
def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        resp = db.client.table("profiles").select("*").eq("id", user_id).execute()
        return resp.data[0] if resp.data else None
    except:
        return None

def create_user_profile(user_id: str, email: str, first_name: str, last_name: str, role: str = "user") -> bool:
    try:
        db.client.table("profiles").insert({"id": user_id, "email": email, "first_name": first_name, "last_name": last_name, "role": role}).execute()
        return True
    except:
        return False

def get_user_projects(user_id: str) -> List[Dict[str, Any]]:
    try:
        resp = db.client.table("projects").select("*").eq("user_id", user_id).execute()
        return resp.data if resp.data else []
    except:
        return []

# PROJECTS
def create_project(user_id: str, brand_name: str, domain: str, region: str = "Ukraine") -> Optional[Dict[str, Any]]:
    try:
        resp = db.client.table("projects").insert({"user_id": user_id, "brand_name": brand_name, "domain": domain, "region": region, "status": "trial"}).execute()
        return resp.data[0] if resp.data else None
    except:
        return None

def get_project_keywords(project_id: str) -> List[Dict[str, Any]]:
    try:
        resp = db.client.table("keywords").select("*").eq("project_id", project_id).eq("is_active", True).execute()
        return resp.data if resp.data else []
    except:
        return []

def create_keywords(project_id: str, keywords_list: List[str]) -> bool:
    try:
        data = [{"project_id": project_id, "keyword_text": kw, "is_active": True} for kw in keywords_list]
        db.client.table("keywords").insert(data).execute()
        return True
    except:
        return False

# SCAN RESULTS
@lru_cache(maxsize=32)
def get_scan_results(project_id: str, provider: Optional[str] = None):
    try:
        query = db.client.table("scan_results").select("*").eq("project_id", project_id)
        if provider:
            query = query.eq("provider", provider)
        resp = query.execute()
        return resp.data if resp.data else []
    except:
        return []

# OFFICIAL ASSETS
def get_official_assets(project_id: str) -> List[str]:
    try:
        resp = db.client.table("official_assets").select("domain_or_url").eq("project_id", project_id).execute()
        return [item["domain_or_url"] for item in resp.data] if resp.data else []
    except:
        return []

def add_official_asset(project_id: str, domain_or_url: str, asset_type: str = "website") -> bool:
    try:
        db.client.table("official_assets").insert({"project_id": project_id, "domain_or_url": domain_or_url, "type": asset_type}).execute()
        return True
    except:
        return False

def clear_all_caches():
    get_scan_results.cache_clear()
