"""
Модуль аутентифікації
Оптимізація: спрощена логіка, менше rerun()
"""

import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from database import db, get_user_profile, create_user_profile, get_user_projects, clear_all_caches
import time


# Cookie Manager (глобальний)
cookie_manager = stx.CookieManager()


def initialize_session_state():
    """Ініціалізація session state змінних"""
    defaults = {
        "user": None,
        "user_details": {},
        "role": "user",
        "current_project": None,
        "current_page": "Дашборд",
        "projects": [],
        "generated_prompts": [],
        "onboarding_step": 2,
        "focus_keyword_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_user_role_and_details(user_id: str) -> Tuple[str, Dict[str, Any]]:
    """Отримати роль та деталі користувача"""
    profile = get_user_profile(user_id)

    if profile:
        return profile.get("role", "user"), {
            "first_name": profile.get("first_name"),
            "last_name": profile.get("last_name"),
        }

    return "user", {}


def load_user_project(user_id: str) -> bool:
    """Завантажити проект користувача"""
    projects = get_user_projects(user_id)

    if projects:
        st.session_state["projects"] = projects
        st.session_state["current_project"] = projects[0]  # Перший проект
        return True

    return False


def check_session():
    """Перевірити сесію користувача через cookie"""
    if st.session_state["user"] is not None:
        return  # Вже авторизований

    time.sleep(0.1)  # Даємо час cookie manager
    token = cookie_manager.get("virshi_auth_token")

    if not token:
        return

    try:
        res = db.client.auth.get_user(token)

        if getattr(res, "user", None):
            st.session_state["user"] = res.user
            role, details = get_user_role_and_details(res.user.id)
            st.session_state["role"] = role
            st.session_state["user_details"] = details
            load_user_project(res.user.id)
        else:
            cookie_manager.delete("virshi_auth_token")

    except Exception:
        cookie_manager.delete("virshi_auth_token")


def login_user(email: str, password: str) -> bool:
    """Авторизація користувача"""
    try:
        res = db.client.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })

        if not res.user:
            st.error("❌ Невірний email або пароль")
            return False

        # Зберігаємо в session state
        st.session_state["user"] = res.user

        # Зберігаємо token в cookie
        cookie_manager.set(
            "virshi_auth_token",
            res.session.access_token,
            expires_at=datetime.now() + timedelta(days=7)
        )

        # Завантажуємо профіль
        role, details = get_user_role_and_details(res.user.id)
        st.session_state["role"] = role
        st.session_state["user_details"] = details

        # Завантажуємо проекти
        load_user_project(res.user.id)

        st.success("✅ Вхід успішний!")
        return True

    except Exception as e:
        st.error(f"❌ Помилка входу: {str(e)}")
        return False


def register_user(email: str, password: str, first_name: str, last_name: str) -> bool:
    """Реєстрація нового користувача"""
    try:
        res = db.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "first_name": first_name,
                    "last_name": last_name
                }
            }
        })

        if not res.user:
            st.error("❌ Не вдалося створити акаунт")
            return False

        # Створюємо профіль
        create_user_profile(
            user_id=res.user.id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="user"
        )

        # Якщо є сесія (autoconfirm увімкнено)
        if res.session:
            st.session_state["user"] = res.user
            cookie_manager.set(
                "virshi_auth_token",
                res.session.access_token,
                expires_at=datetime.now() + timedelta(days=7)
            )

            role, details = get_user_role_and_details(res.user.id)
            st.session_state["role"] = role
            st.session_state["user_details"] = details

            st.success("✅ Реєстрація успішна! Виконуємо вхід...")
            return True
        else:
            st.success("✅ Реєстрація успішна! Перевірте email для підтвердження.")
            return False

    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            st.warning("⚠️ Користувач вже існує. Спробуйте увійти.")
        else:
            st.error(f"❌ Помилка реєстрації: {error_msg}")
        return False


def logout():
    """Вихід з системи"""
    # 1. Видаляємо cookie
    try:
        cookie_manager.delete("virshi_auth_token")
    except:
        pass

    # 2. Вихід з Supabase
    try:
        db.client.auth.sign_out()
    except:
        pass

    # 3. Очищаємо кеші
    clear_all_caches()

    # 4. Очищаємо session state
    st.session_state.clear()
    initialize_session_state()

    # 5. Перезавантаження
    time.sleep(0.5)
    st.rerun()


def render_login_page():
    """Рендер сторінки логіну/реєстрації"""
    col_left, col_center, col_right = st.columns([1, 1.5, 1])

    with col_center:
        # Логотип
        st.markdown(
            '<div style="text-align: center;">'
            '<img src="https://raw.githubusercontent.com/virshi-ai/image/refs/heads/main/logo-removebg-preview.png" width="180">'
            '</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Таби
        tab_login, tab_register = st.tabs(["🔑 Вхід", "📝 Реєстрація"])

        # === ВХІД ===
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Пароль", type="password", key="login_password")

                submit = st.form_submit_button("Увійти", use_container_width=True)

                if submit:
                    if email and password:
                        if login_user(email, password):
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.warning("⚠️ Введіть email та пароль")

        # === РЕЄСТРАЦІЯ ===
        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Пароль", type="password", key="reg_password")

                col1, col2 = st.columns(2)
                reg_first = col1.text_input("Ім'я", key="reg_first")
                reg_last = col2.text_input("Прізвище", key="reg_last")

                submit = st.form_submit_button("Зареєструватися", use_container_width=True)

                if submit:
                    if reg_email and reg_password and reg_first:
                        if register_user(reg_email, reg_password, reg_first, reg_last):
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("⚠️ Заповніть всі обов'язкові поля")
