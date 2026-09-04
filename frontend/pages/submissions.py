from math import ceil
from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import list_problems, list_submissions, list_users
    from ..session import (
        get_current_user,
        get_selected_submission,
        is_admin,
        set_selected_submission,
    )
    from ..ui import require_login, show_api_message
else:
    from api_client import list_problems, list_submissions, list_users
    from session import (
        get_current_user,
        get_selected_submission,
        is_admin,
        set_selected_submission,
    )
    from ui import require_login, show_api_message


_FILTERS_KEY = "submission_filters"
_TOTAL_KEY = "submission_filter_total"
_VIEW_KEY = "submission_page_view"
_RETURN_KEY = "submission_return_view"
_DETAIL_MODE_KEY = "submission_detail_mode"


def _load_problem_choices() -> list[dict[str, Any]]:
    status_code, body = list_problems()
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return []
    data = body.get("data")
    if not isinstance(data, list):
        st.error("后端题目列表响应格式异常。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def _load_user_choices() -> list[dict[str, Any]]:
    if not is_admin():
        current_user = get_current_user()
        return [current_user] if isinstance(current_user, dict) else []

    status_code, body = list_users()
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return []
    data = body.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        st.error("后端用户列表响应格式异常。")
        return []
    return [user for user in data["users"] if isinstance(user, dict)]


def _choice_index(values: list[str | None], current: Any) -> int:
    return values.index(current) if current in values else 0


def render_filters() -> dict[str, Any]:
    """
    返回查询条件：
    user_id / problem_id / status / page / page_size
    """
    current_user = get_current_user() or {}
    current_user_id = str(current_user.get("user_id", ""))
    defaults = st.session_state.get(
        _FILTERS_KEY,
        {
            "user_id": current_user_id,
            "problem_id": None,
            "status": None,
            "page": 1,
            "page_size": 10,
        },
    )

    users = _load_user_choices()
    problems = _load_problem_choices()
    user_labels: dict[str, str | None] = {
        f"{user.get('username', 'unknown')} · {user.get('user_id', '')}": str(
            user.get("user_id", "")
        )
        for user in users
        if isinstance(user.get("user_id"), str) and user.get("user_id")
    }
    if is_admin():
        user_labels = {"不限": None, **user_labels}
    problem_labels: dict[str, str | None] = {
        "不限": None,
        **{
            f"{problem.get('id', '')} · {problem.get('title', '')}": str(
                problem.get("id", "")
            )
            for problem in problems
            if isinstance(problem.get("id"), str) and problem.get("id")
        },
    }
    status_labels = {"不限": None, "pending": "pending", "success": "success", "error": "error"}

    user_values = list(user_labels.values())
    problem_values = list(problem_labels.values())
    status_values = list(status_labels.values())
    previous_total = int(st.session_state.get(_TOTAL_KEY, 0))
    previous_page_size = int(defaults.get("page_size") or 10)
    previous_max_page = max(1, ceil(previous_total / previous_page_size))

    with st.form("submission_filters_form"):
        selected_user_label = st.selectbox(
            "user_id",
            list(user_labels),
            index=_choice_index(user_values, defaults.get("user_id")),
            disabled=not is_admin(),
        )
        selected_problem_label = st.selectbox(
            "problem_id",
            list(problem_labels),
            index=_choice_index(problem_values, defaults.get("problem_id")),
        )
        selected_status_label = st.selectbox(
            "status",
            list(status_labels),
            index=_choice_index(status_values, defaults.get("status")),
        )
        page_column, size_column = st.columns(2)
        page_options = list(range(1, previous_max_page + 1))
        page = int(
            page_column.selectbox(
                "page",
                page_options,
                index=min(max(int(defaults.get("page") or 1), 1), previous_max_page)
                - 1,
            )
        )
        page_sizes = [5, 10, 20, 50]
        default_page_size = int(defaults.get("page_size") or 10)
        page_size = int(
            size_column.selectbox(
                "page_size",
                page_sizes,
                index=(
                    page_sizes.index(default_page_size)
                    if default_page_size in page_sizes
                    else 1
                ),
            )
        )
        submitted = st.form_submit_button("查询评测列表", use_container_width=True)

    filters = {
        "user_id": user_labels[selected_user_label],
        "problem_id": problem_labels[selected_problem_label],
        "status": status_labels[selected_status_label],
        "page": page,
        "page_size": page_size,
    }
    if not is_admin():
        filters["user_id"] = current_user_id
    if submitted or _FILTERS_KEY not in st.session_state:
        st.session_state[_FILTERS_KEY] = filters
    saved_filters = dict(st.session_state[_FILTERS_KEY])
    if not is_admin():
        saved_filters["user_id"] = current_user_id
        st.session_state[_FILTERS_KEY] = saved_filters
    return saved_filters


def load_submissions(
    *,
    user_id: str | None = None,
    problem_id: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """加载评测列表并返回 total 和 submissions。"""
    status_code, body = list_submissions(
        user_id=user_id,
        problem_id=problem_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return 0, []
    data = body.get("data")
    if not isinstance(data, dict):
        st.error("后端评测列表响应格式异常。")
        return 0, []
    total = data.get("total")
    rows = data.get("submissions")
    if not isinstance(total, int) or not isinstance(rows, list):
        st.error("后端评测列表响应缺少有效的 total 或 submissions 字段。")
        return 0, []
    return total, [row for row in rows if isinstance(row, dict)]


def render_submission_table(submissions: list[dict[str, Any]]) -> None:
    """展示评测列表。"""
    if not submissions:
        st.info("没有符合筛选条件的评测结果。")
        return
    rows = [
        {
            "submission_id": submission.get("submission_id", ""),
            "status": submission.get("status", ""),
            "score": submission.get("score")
            if submission.get("score") is not None
            else "—",
            "counts": submission.get("counts")
            if submission.get("counts") is not None
            else "—",
        }
        for submission in submissions
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _open_submission(submission_id: str, mode: str) -> None:
    set_selected_submission(submission_id)
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_RETURN_KEY] = "list"
    st.session_state[_DETAIL_MODE_KEY] = mode
    st.rerun()


def render_submission_selector(submissions: list[dict[str, Any]]) -> None:
    """选择 submission 后进入评测结果或评测日志。"""
    valid_ids = [
        submission.get("submission_id")
        for submission in submissions
        if isinstance(submission.get("submission_id"), str)
        and submission.get("submission_id")
    ]
    if not valid_ids:
        return
    selected_submission_id = st.selectbox("submission_id", valid_ids)
    result_column, log_column = st.columns(2)
    if result_column.button("查询评测结果", type="primary", use_container_width=True):
        _open_submission(selected_submission_id, "result")
    if log_column.button("查询评测日志", use_container_width=True):
        _open_submission(selected_submission_id, "log")


def render_page() -> None:
    """评测结果页面入口。"""
    if not require_login():
        return

    if (
        st.session_state.get(_VIEW_KEY) == "detail"
        and get_selected_submission() is not None
    ):
        if __package__ == "frontend.pages":
            from . import submission_detail
        else:
            from pages import submission_detail
        submission_detail.render_page()
        return

    st.subheader("评测列表")
    filters = render_filters()
    if filters.get("user_id") is None and filters.get("problem_id") is None:
        st.error("user_id 和 problem_id 不能同时为空。")
        return

    total, rows = load_submissions(**filters)
    st.session_state[_TOTAL_KEY] = total
    page_size = int(filters.get("page_size") or 10)
    current_page = int(filters.get("page") or 1)
    max_page = max(1, ceil(total / page_size))
    if current_page > max_page:
        filters["page"] = max_page
        st.session_state[_FILTERS_KEY] = filters
        st.rerun()
    st.caption(f"total: {total} · page: {current_page}/{max_page}")
    render_submission_table(rows)
    render_submission_selector(rows)
