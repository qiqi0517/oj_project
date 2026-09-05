from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import get_user
    from ..session import clear_current_user, get_current_user, set_current_user
    from ..ui import render_user_summary, require_login, show_api_message
    from .auth import render_logout_button
else:
    from api_client import get_user
    from pages.auth import render_logout_button
    from session import clear_current_user, get_current_user, set_current_user
    from ui import render_user_summary, require_login, show_api_message


def load_current_user_profile() -> dict[str, Any] | None:
    """Refresh the current user's public data through the API."""
    current_user = get_current_user()
    if current_user is None:
        return None

    user_id = current_user.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        st.error("当前 Session 中没有有效的 user_id，请重新登录。")
        clear_current_user()
        return None

    status_code, body = get_user(user_id)
    if not show_api_message(status_code, body, show_success=False):
        if status_code in {401, 403}:
            clear_current_user()
        return None

    user = body.get("data")
    if not isinstance(user, dict):
        st.error("API 响应格式无效：data 应包含用户对象。")
        return None

    set_current_user(user)
    return user


def render_profile(user: dict[str, Any]) -> None:
    """Render the current user's public API fields."""
    render_user_summary(user)


def render_page() -> None:
    """Render the profile page."""
    if not require_login():
        return

    user = load_current_user_profile()
    if user is not None:
        render_profile(user)

    st.divider()
    st.subheader("账号操作")
    render_logout_button()
