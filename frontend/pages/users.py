from math import ceil
from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import list_users, update_user_role
    from ..session import get_current_user, set_current_user
    from ..ui import require_admin, show_api_message
else:
    from api_client import list_users, update_user_role
    from session import get_current_user, set_current_user
    from ui import require_admin, show_api_message


_PAGE_KEY = "users_page"
_PAGE_SIZE_KEY = "users_page_size"
_ROLE_NAMES = {"user": "普通用户", "admin": "管理员", "banned": "已禁用"}


def load_users(
    page: int | None,
    page_size: int | None,
) -> tuple[int, list[dict[str, Any]]]:
    """加载用户列表并返回 total 和 users。"""
    status_code, body = list_users(page=page, page_size=page_size)
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return 0, []

    data = body.get("data")
    if not isinstance(data, dict):
        st.error("后端用户列表响应格式异常。")
        return 0, []

    total = data.get("total")
    users = data.get("users")
    if not isinstance(total, int) or not isinstance(users, list):
        st.error("后端用户列表响应缺少有效的 total 或 users 字段。")
        return 0, []

    valid_users = [user for user in users if isinstance(user, dict)]
    return total, valid_users


def render_user_table(users: list[dict[str, Any]]) -> None:
    """展示用户列表。"""
    if not users:
        st.info("当前没有可显示的用户。")
        return

    rows = [
        {
            "用户 ID": user.get("user_id", ""),
            "用户名": user.get("username", ""),
            "角色": _ROLE_NAMES.get(str(user.get("role")), user.get("role", "")),
            "加入时间": user.get("join_time", ""),
            "提交次数": user.get("submit_count", 0),
            "通过题目数": user.get("resolve_count", 0),
        }
        for user in users
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_role_editor(users: list[dict[str, Any]]) -> None:
    """选择用户并修改 role。"""
    if not users:
        return

    user_by_label = {
        f"{user.get('username', '未知用户')}（{user.get('user_id', '')}）": user
        for user in users
    }
    selected_label = st.selectbox("选择用户", list(user_by_label))
    selected_user = user_by_label[selected_label]
    current_role = str(selected_user.get("role", "user"))
    roles = ["user", "admin", "banned"]

    with st.form("role_editor"):
        role = st.selectbox(
            "新角色",
            roles,
            index=roles.index(current_role) if current_role in roles else 0,
            format_func=lambda value: _ROLE_NAMES[value],
        )
        submitted = st.form_submit_button("更新角色", type="primary")

    if not submitted:
        return

    user_id = selected_user.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        st.error("所选用户缺少有效的用户 ID。")
        return
    if role == current_role:
        st.info("用户角色没有变化。")
        return

    status_code, body = update_user_role(user_id, role)
    if not show_api_message(status_code, body):
        return

    current_user = get_current_user()
    if current_user is not None and current_user.get("user_id") == user_id:
        updated_current_user = current_user.copy()
        updated_current_user["role"] = role
        set_current_user(updated_current_user)
    st.rerun()


def render_pagination(total: int) -> tuple[int | None, int | None]:
    """管理员用户列表分页控件。"""
    if _PAGE_SIZE_KEY not in st.session_state:
        st.session_state[_PAGE_SIZE_KEY] = 10
    page_size = int(
        st.selectbox(
            "每页数量",
            [5, 10, 20, 50],
            key=_PAGE_SIZE_KEY,
        )
    )
    max_page = max(1, ceil(total / page_size))

    current_page = int(st.session_state.get(_PAGE_KEY, 1))
    st.session_state[_PAGE_KEY] = min(max(1, current_page), max_page)
    page = int(
        st.number_input(
            "页码",
            min_value=1,
            max_value=max_page,
            step=1,
            key=_PAGE_KEY,
        )
    )
    st.caption(f"共 {total} 位用户，第 {page} / {max_page} 页")
    return page, page_size


def render_page() -> None:
    """用户管理页面入口。"""
    if not require_admin():
        return

    requested_page = int(st.session_state.get(_PAGE_KEY, 1))
    requested_page_size = int(st.session_state.get(_PAGE_SIZE_KEY, 10))
    total, users = load_users(requested_page, requested_page_size)
    page, page_size = render_pagination(total)
    if page != requested_page or page_size != requested_page_size:
        st.rerun()

    render_user_table(users)
    st.divider()
    st.subheader("修改用户角色")
    render_role_editor(users)
