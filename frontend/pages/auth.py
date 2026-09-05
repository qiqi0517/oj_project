from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import login, logout, register_user
    from ..session import clear_current_user, is_logged_in, set_current_user
    from ..ui import show_api_message
else:
    from api_client import login, logout, register_user
    from session import clear_current_user, is_logged_in, set_current_user
    from ui import show_api_message


_AUTH_NOTICE_KEY = "auth_notice"


def _login_user_from_response(
    status_code: int | None,
    body: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if status_code != 200 or body is None or body.get("code") != 200:
        return None

    user = body.get("data")
    if not isinstance(user, dict):
        return None

    user_id = user.get("user_id")
    username = user.get("username")
    role = user.get("role")
    if (
        not isinstance(user_id, str)
        or not user_id
        or not isinstance(username, str)
        or not username
        or role not in {"user", "admin", "banned"}
    ):
        return None
    return user


def render_login_form() -> None:
    """Render the sign-in form."""
    if is_logged_in():
        st.info("当前已有用户登录，请先退出再切换账号。")
        return

    with st.form("login_form"):
        username = st.text_input("用户名", autocomplete="username")
        password = st.text_input(
            "密码",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("登录", use_container_width=True)

    if not submitted:
        return
    normalized_username = (username or "").strip()
    if not normalized_username or not password:
        st.error("username 和 password 均为必填项。")
        return

    status_code, body = login(normalized_username, password)
    if not show_api_message(status_code, body, show_success=False):
        return
    user = _login_user_from_response(status_code, body)
    if user is None:
        st.error("API 响应格式无效：data 中没有有效的用户信息。")
        return
    if not show_api_message(status_code, body):
        return

    set_current_user(user)
    st.session_state[_AUTH_NOTICE_KEY] = "登录成功。"
    st.rerun()


def render_register_form() -> None:
    """Render the registration form."""
    if is_logged_in():
        st.info("当前已有用户登录，请先退出再注册账号。")
        return

    with st.form("register_form"):
        username = st.text_input("用户名", autocomplete="username")
        password = st.text_input(
            "密码",
            type="password",
            autocomplete="new-password",
        )
        password_confirmation = st.text_input(
            "确认密码",
            type="password",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button("注册", use_container_width=True)

    if not submitted:
        return

    normalized_username = (username or "").strip()
    if not 3 <= len(normalized_username) <= 40:
        st.error("username 长度必须为 3 至 40 个字符。")
        return
    if not password or len(password) < 6:
        st.error("password 至少需要 6 个字符。")
        return
    if password != password_confirmation:
        st.error("password_confirmation 与 password 不一致。")
        return

    status_code, body = register_user(normalized_username, password)
    if show_api_message(status_code, body):
        st.info("注册成功后不会自动登录，请返回登录页面。")


def render_logout_button() -> None:
    """Render the sign-out action."""
    if not is_logged_in():
        st.info("当前没有已登录用户。")
        return

    st.write("退出登录后，当前 Session 将无法继续访问受保护的 API。")
    if not st.button("退出登录", type="primary", use_container_width=True):
        return

    status_code, body = logout()
    if not show_api_message(status_code, body):
        return

    clear_current_user()
    st.session_state[_AUTH_NOTICE_KEY] = "已退出登录。"
    st.rerun()


def render_page() -> None:
    """Render authentication actions."""
    if is_logged_in():
        render_logout_button()
        return

    login_tab, register_tab = st.tabs(["登录", "注册"])
    with login_tab:
        render_login_form()
    with register_tab:
        render_register_form()


def pop_auth_notice() -> str | None:
    """Return and remove a one-time authentication notice."""
    return st.session_state.pop(_AUTH_NOTICE_KEY, None)
