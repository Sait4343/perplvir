"""
Сторінка AI звітів та рекомендацій
Оптимізація: кешування, асинхронні запити
"""

import streamlit as st
from typing import Optional
from n8n.webhooks import trigger_ai_recommendation
from components import render_empty_state


def initialize_reports_state():
    """Ініціалізація стану сторінки"""
    if "report_category" not in st.session_state:
        st.session_state["report_category"] = "overview"
    if "report_context" not in st.session_state:
        st.session_state["report_context"] = ""
    if "last_report" not in st.session_state:
        st.session_state["last_report"] = None


def render_category_selector():
    """Вибір категорії звіту"""
    categories = {
        "overview": {
            "title": "📊 Загальний огляд",
            "description": "Загальний аналіз видимості та позиціонування"
        },
        "seo": {
            "title": "🔍 SEO рекомендації",
            "description": "Як покращити SEO для AI-пошуку"
        },
        "content": {
            "title": "✍️ Контент-стратегія",
            "description": "Які теми та формати створювати"
        },
        "competitors": {
            "title": "👥 Конкурентний аналіз",
            "description": "Порівняння з конкурентами та можливості"
        },
        "sentiment": {
            "title": "💬 Репутаційний аналіз",
            "description": "Аналіз тональності та рекомендації"
        }
    }

    st.markdown("### Оберіть тип звіту")

    cols = st.columns(len(categories))

    for idx, (key, data) in enumerate(categories.items()):
        with cols[idx]:
            if st.button(
                data["title"],
                key=f"cat_{key}",
                use_container_width=True,
                type="primary" if st.session_state.get("report_category") == key else "secondary"
            ):
                st.session_state["report_category"] = key
                st.rerun()

    # Опис обраної категорії
    selected = st.session_state.get("report_category", "overview")
    st.info(f"💡 {categories[selected]['description']}")


def render_context_form():
    """Форма додаткового контексту"""
    st.markdown("### Додатковий контекст (опціонально)")

    context = st.text_area(
        "Додайте специфічні питання або контекст для звіту",
        placeholder="Наприклад: Хочу збільшити видимість у запитах про кредити для бізнесу...",
        height=100,
        key="context_input"
    )

    st.session_state["report_context"] = context


def render_generate_button(project: dict):
    """Кнопка генерації звіту"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🤖 Згенерувати AI звіт",
            type="primary",
            use_container_width=True
        ):
            generate_report(project)


def generate_report(project: dict):
    """Генерація звіту через AI"""
    user = st.session_state.get("user")
    category = st.session_state.get("report_category", "overview")
    context = st.session_state.get("report_context", "")

    # Формуємо контекст
    full_context = f"""
    Категорія звіту: {category}
    Додатковий контекст: {context if context else 'Немає'}
    """

    with st.spinner("🤖 AI генерує детальний звіт... Це може зайняти до 2 хвилин."):
        html_report = trigger_ai_recommendation(
            user=user,
            project=project,
            category=category,
            context_text=full_context
        )

        if html_report and not html_report.startswith("<p style='color:red"):
            st.session_state["last_report"] = {
                "category": category,
                "html": html_report,
                "timestamp": st.session_state.get("user", {})
            }
            st.success("✅ Звіт готовий!")
            st.rerun()
        else:
            st.error("❌ Помилка генерації звіту. Спробуйте ще раз.")


def render_report_output():
    """Відображення згенерованого звіту"""
    last_report = st.session_state.get("last_report")

    if not last_report:
        return

    st.markdown("---")
    st.markdown("## 📄 Згенерований звіт")

    # Кнопки дій
    col1, col2 = st.columns([4, 1])

    with col2:
        if st.button("🔄 Новий звіт", use_container_width=True):
            st.session_state["last_report"] = None
            st.rerun()

    # Відображення HTML
    st.markdown(
        '<div class="ai-response-box">' + last_report["html"] + '</div>',
        unsafe_allow_html=True
    )

    # Кнопка експорту (placeholder)
    st.markdown("---")
    st.download_button(
        label="📥 Завантажити звіт (HTML)",
        data=last_report["html"],
        file_name=f"virshi_report_{last_report['category']}.html",
        mime="text/html"
    )


def render_reports_page():
    """Головна функція сторінки звітів"""
    initialize_reports_state()

    project = st.session_state.get("current_project")

    if not project:
        render_empty_state(
            icon="📊",
            title="Проект не обрано",
            description="Оберіть проект у сайдбарі"
        )
        return

    st.title("📊 AI Звіти та Рекомендації")

    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <h3 style='margin: 0; color: white;'>🤖 AI-асистент для GEO</h3>
            <p style='margin: 10px 0 0 0; opacity: 0.9;'>
                Отримайте персоналізовані рекомендації на основі аналізу вашої видимості в AI-пошуку
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Якщо є звіт - показуємо його
    if st.session_state.get("last_report"):
        render_report_output()
        return

    # Інакше - форма генерації
    render_category_selector()

    st.markdown("---")

    render_context_form()

    st.markdown("---")

    render_generate_button(project)

    # Приклади питань
    st.markdown("---")
    st.markdown("### 💡 Приклади питань для AI")

    examples = [
        "Як покращити видимість у запитах про [ваш продукт]?",
        "Чому конкуренти рейтингуються вище за мене?",
        "Які теми контенту створити для кращого ранжування?",
        "Як змінити негативну тональність згадок?",
        "Які офіційні джерела додати для довіри?"
    ]

    for example in examples:
        st.caption(f"• {example}")
