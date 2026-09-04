from typing import Any

import requests
import streamlit as st

_API_SESSION_KEY = "api_session"
_CURRENT_USER_KEY = "current_user"
_SELECTED_PROBLEM_KEY = "selected_problem_id"
_SELECTED_SUBMISSION_KEY = "selected_submission_id"
_PAGE_STATE_KEYS = (
    "navigation_page",
    "problem_page_view",
    "problem_notice",
    "submission_page_view",
    "submission_return_view",
    "submission_detail_mode",
    "submission_notice",
    "submission_filters",
    "submission_filter_total",
    "users_page",
    "users_page_size",
    "selected_user",
)


def init_session_state() -> None:
    """初始化本次 Streamlit 会话需要的状态。"""
    if _API_SESSION_KEY not in st.session_state:
        st.session_state[_API_SESSION_KEY] = requests.Session()
    if _CURRENT_USER_KEY not in st.session_state:
        st.session_state[_CURRENT_USER_KEY] = None
    if _SELECTED_PROBLEM_KEY not in st.session_state:
        st.session_state[_SELECTED_PROBLEM_KEY] = None
    if _SELECTED_SUBMISSION_KEY not in st.session_state:
        st.session_state[_SELECTED_SUBMISSION_KEY] = None


def get_api_session() -> requests.Session:
    """获取当前 Streamlit 用户独立使用的 requests.Session。"""
    init_session_state()
    return st.session_state[_API_SESSION_KEY]


def get_current_user() -> dict[str, Any] | None:
    """获取当前前端保存的用户信息。"""
    init_session_state()
    return st.session_state[_CURRENT_USER_KEY]


def set_current_user(user: dict[str, Any]) -> None:
    """登录成功后保存当前用户信息。"""
    init_session_state()
    st.session_state[_CURRENT_USER_KEY] = user.copy()


def clear_current_user() -> None:
    """退出登录后清空当前用户信息。"""
    init_session_state()
    st.session_state[_CURRENT_USER_KEY] = None
    st.session_state[_SELECTED_PROBLEM_KEY] = None
    st.session_state[_SELECTED_SUBMISSION_KEY] = None
    for key in _PAGE_STATE_KEYS:
        st.session_state.pop(key, None)
    get_api_session().cookies.clear()


def is_logged_in() -> bool:
    """当前前端是否记录了登录用户。"""
    return get_current_user() is not None


def is_admin() -> bool:
    """当前用户是否为管理员。"""
    user = get_current_user()
    return user is not None and user.get("role") == "admin"


def set_selected_problem(problem_id: str | None) -> None:
    """保存当前正在查看的题目编号。"""
    init_session_state()
    st.session_state[_SELECTED_PROBLEM_KEY] = problem_id


def get_selected_problem() -> str | None:
    """获取当前正在查看的题目编号。"""
    init_session_state()
    return st.session_state[_SELECTED_PROBLEM_KEY]


def set_selected_submission(submission_id: str | None) -> None:
    """保存当前正在查看的 submission id。"""
    init_session_state()
    st.session_state[_SELECTED_SUBMISSION_KEY] = submission_id


def get_selected_submission() -> str | None:
    """获取当前正在查看的 submission id。"""
    init_session_state()
    return st.session_state[_SELECTED_SUBMISSION_KEY]
