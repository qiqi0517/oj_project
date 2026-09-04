from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import login, logout
    from ..session import clear_current_user, is_logged_in, set_current_user
    from ..ui import show_api_message
else:
    from api_client import login, logout
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
    """登录表单。"""
    if is_logged_in():
        st.info("当前已有用户登录。如需切换账号，请先退出登录。")
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
        st.error("请输入用户名和密码。")
        return

    status_code, body = login(normalized_username, password)
    user = _login_user_from_response(status_code, body)
    if user is None:
        if status_code == 200:
            st.error("后端登录响应缺少有效的用户信息。")
        else:
            show_api_message(status_code, body)
        return
    if not show_api_message(status_code, body):
        return

    set_current_user(user)
    st.session_state[_AUTH_NOTICE_KEY] = "登录成功。"
    st.rerun()


def render_register_form() -> None:
    """注册表单。"""
    st.info("用户注册将在阶段 3 接入。")


def render_logout_button() -> None:
    """退出登录按钮。"""
    if not is_logged_in():
        st.info("当前没有已登录用户。")
        return

    st.write("退出后，当前浏览器会话将无法继续访问受保护接口。")
    if not st.button("确认退出登录", type="primary", use_container_width=True):
        return

    status_code, body = logout()
    if not show_api_message(status_code, body):
        return

    clear_current_user()
    st.session_state[_AUTH_NOTICE_KEY] = "已安全退出登录。"
    st.rerun()


def render_page() -> None:
    """认证页面入口。"""
    if is_logged_in():
        render_logout_button()
        return

    login_tab, register_tab = st.tabs(["登录", "注册"])
    with login_tab:
        render_login_form()
    with register_tab:
        render_register_form()


def pop_auth_notice() -> str | None:
    """取出只展示一次的认证结果提示。"""
    return st.session_state.pop(_AUTH_NOTICE_KEY, None)
