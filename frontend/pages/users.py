from math import ceil
from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import get_user, list_users, update_user_role
    from ..session import get_current_user, set_current_user
    from ..ui import (
        format_role,
        get_selected_row_index,
        render_user_summary,
        require_admin,
        show_api_message,
    )
else:
    from api_client import get_user, list_users, update_user_role
    from session import get_current_user, set_current_user
    from ui import (
        format_role,
        get_selected_row_index,
        render_user_summary,
        require_admin,
        show_api_message,
    )


_PAGE_KEY = "users_page"
_PAGE_SIZE_KEY = "users_page_size"
_SELECTED_USER_KEY = "selected_user"


def load_users(
    page: int | None,
    page_size: int | None,
) -> tuple[int, list[dict[str, Any]]]:
    """Load total and users through GET /api/users/."""
    status_code, body = list_users(page=page, page_size=page_size)
    if not show_api_message(status_code, body, show_success=False):
        return 0, []

    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应为对象。")
        return 0, []

    total = data.get("total")
    users = data.get("users")
    if not isinstance(total, int) or not isinstance(users, list):
        st.error("API 响应格式无效：total 应为 int，users 应为列表。")
        return 0, []

    valid_users = [user for user in users if isinstance(user, dict)]
    return total, valid_users


def render_user_table(users: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Render user-list fields exactly as named by the API."""
    if not users:
        st.info("暂无用户数据。")
        return None

    rows = [
        {
            "用户编号": user.get("user_id", ""),
            "用户名": user.get("username", ""),
            "用户身份": format_role(user.get("role")),
            "注册时间": user.get("join_time", ""),
            "提交次数": user.get("submit_count", 0),
            "通过题数": user.get("resolve_count", 0),
        }
        for user in users
    ]
    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="user_list_table",
    )
    selected_index = get_selected_row_index(event)
    if selected_index is None or selected_index >= len(users):
        return None
    return users[selected_index]


def load_user_detail(user_id: str) -> dict[str, Any] | None:
    """Load a user through GET /api/users/{user_id}."""
    status_code, body = get_user(user_id)
    if not show_api_message(status_code, body, show_success=False):
        return None
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应包含用户对象。")
        return None
    return data


def render_role_editor(selected_user: dict[str, Any] | None) -> None:
    """Select a user and update role through the API."""
    if selected_user is None:
        st.info("请先从用户列表中选择并查看一名用户。")
        return

    current_role = str(selected_user.get("role", "user"))
    roles = ["user", "admin", "banned"]
    st.caption(
        f"当前用户：{selected_user.get('username', '未知用户')} · "
        f"用户编号：{selected_user.get('user_id', '未提供')}"
    )

    with st.form("role_editor"):
        role = st.selectbox(
            "用户角色",
            roles,
            index=roles.index(current_role) if current_role in roles else 0,
            format_func=format_role,
        )
        submitted = st.form_submit_button("更新 role", type="primary")

    if not submitted:
        return

    user_id = selected_user.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        st.error("选中的用户没有有效的 user_id。")
        return
    if role == current_role:
        st.info("role 未发生变化。")
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
    """Render the page and page_size query controls."""
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
        st.selectbox(
            "页码",
            list(range(1, max_page + 1)),
            index=st.session_state[_PAGE_KEY] - 1,
            key=_PAGE_KEY,
        )
    )
    st.caption(f"总数：{total} · 第 {page}/{max_page} 页")
    return page, page_size


def render_user_selector(
    selected_user: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Select a list item and display its public fields."""
    st.caption("请在列表左侧选中一条用户记录。")
    if st.button(
        "查看选中用户",
        type="primary",
        use_container_width=True,
        disabled=selected_user is None,
    ):
        selected_user_id = selected_user.get("user_id") if selected_user else None
        if not isinstance(selected_user_id, str) or not selected_user_id:
            st.error("选中的用户没有有效的 user_id。")
        else:
            loaded_user = load_user_detail(selected_user_id)
            if loaded_user is not None:
                st.session_state[_SELECTED_USER_KEY] = loaded_user

    detailed_user = st.session_state.get(_SELECTED_USER_KEY)
    if isinstance(detailed_user, dict):
        render_user_summary(detailed_user)
        return detailed_user
    return None


def render_page() -> None:
    """Render the admin user-management page."""
    if not require_admin():
        return

    requested_page = int(st.session_state.get(_PAGE_KEY, 1))
    requested_page_size = int(st.session_state.get(_PAGE_SIZE_KEY, 10))
    total, users = load_users(requested_page, requested_page_size)
    page, page_size = render_pagination(total)
    if page != requested_page or page_size != requested_page_size:
        st.rerun()

    selected_user = render_user_table(users)
    detailed_user = render_user_selector(selected_user)
    st.divider()
    st.subheader("更新 role")
    render_role_editor(detailed_user)
