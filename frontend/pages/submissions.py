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
    from ..ui import (
        format_submission_status,
        get_selected_row_index,
        require_login,
        show_api_message,
    )
else:
    from api_client import list_problems, list_submissions, list_users
    from session import (
        get_current_user,
        get_selected_submission,
        is_admin,
        set_selected_submission,
    )
    from ui import (
        format_submission_status,
        get_selected_row_index,
        require_login,
        show_api_message,
    )


_FILTERS_KEY = "submission_filters"
_TOTAL_KEY = "submission_filter_total"
_VIEW_KEY = "submission_page_view"
_RETURN_KEY = "submission_return_view"
_DETAIL_MODE_KEY = "submission_detail_mode"


def _load_problem_choices() -> list[dict[str, Any]]:
    status_code, body = list_problems()
    if not show_api_message(status_code, body, show_success=False):
        return []
    data = body.get("data")  # type: ignore
    if not isinstance(data, list):
        st.error("API 响应格式无效：data 应为题目列表。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def _load_user_choices() -> list[dict[str, Any]]:
    if not is_admin():
        current_user = get_current_user()
        return [current_user] if isinstance(current_user, dict) else []

    status_code, body = list_users()
    if not show_api_message(status_code, body, show_success=False):
        return []
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        st.error("API 响应格式无效：data.users 应为列表。")
        return []
    return [user for user in data["users"] if isinstance(user, dict)]


def _choice_index(values: list[str | None], current: Any) -> int:
    return values.index(current) if current in values else 0


def render_filters() -> dict[str, Any]:
    """
    Return the API query parameters:
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
        f"{user.get('username', '未知用户')} · {user.get('user_id', '')}": str(
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
    status_labels = {
        "不限": None,
        "等待评测": "pending",
        "评测完成": "success",
        "评测失败": "error",
    }

    user_values = list(user_labels.values())
    problem_values = list(problem_labels.values())
    status_values = list(status_labels.values())
    previous_total = int(st.session_state.get(_TOTAL_KEY, 0))
    previous_page_size = int(defaults.get("page_size") or 10)
    previous_max_page = max(1, ceil(previous_total / previous_page_size))

    with st.form("submission_filters_form"):
        selected_user_label = st.selectbox(
            "用户",
            list(user_labels),
            index=_choice_index(user_values, defaults.get("user_id")),
            disabled=not is_admin(),
        )
        selected_problem_label = st.selectbox(
            "题目",
            list(problem_labels),
            index=_choice_index(problem_values, defaults.get("problem_id")),
        )
        selected_status_label = st.selectbox(
            "评测状态",
            list(status_labels),
            index=_choice_index(status_values, defaults.get("status")),
        )
        page_column, size_column = st.columns(2)
        page_options = list(range(1, previous_max_page + 1))
        page = int(
            page_column.selectbox(
                "页码",
                page_options,
                index=min(max(int(defaults.get("page") or 1), 1), previous_max_page)
                - 1,
            )
        )
        page_sizes = [5, 10, 20, 50]
        default_page_size = int(defaults.get("page_size") or 10)
        page_size = int(
            size_column.selectbox(
                "每页数量",
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
    """Load total and submissions through GET /api/submissions/."""
    status_code, body = list_submissions(
        user_id=user_id,
        problem_id=problem_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    if not show_api_message(status_code, body, show_success=False):
        return 0, []
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应为对象。")
        return 0, []
    total = data.get("total")
    rows = data.get("submissions")
    if not isinstance(total, int) or not isinstance(rows, list):
        st.error("API 响应格式无效：total 应为 int，submissions 应为列表。")
        return 0, []
    return total, [row for row in rows if isinstance(row, dict)]


def render_submission_table(submissions: list[dict[str, Any]]) -> str | None:
    """Render submission-list fields exactly as named by the API."""
    if not submissions:
        st.info("没有符合筛选条件的评测记录。")
        return None
    rows = [
        {
            "评测编号": submission.get("submission_id", ""),
            "评测状态": format_submission_status(submission.get("status")),
            # Keep nullable numeric columns numeric. A string placeholder such as
            # "—" mixed with integers makes Streamlit/PyArrow conversion fail.
            "得分": submission.get("score"),
            "测试点数": submission.get("counts"),
        }
        for submission in submissions
    ]
    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="submission_list_table",
    )
    selected_index = get_selected_row_index(event)
    if selected_index is None or selected_index >= len(submissions):
        return None
    submission_id = submissions[selected_index].get("submission_id")
    return submission_id if isinstance(submission_id, str) and submission_id else None


def _open_submission(submission_id: str, mode: str) -> None:
    set_selected_submission(submission_id)
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_RETURN_KEY] = "list"
    st.session_state[_DETAIL_MODE_KEY] = mode
    st.rerun()


def render_submission_selector(submission_id: str | None) -> None:
    """Open either the result or judge log for a selected submission."""
    st.caption("请在列表左侧选中一条评测记录。")
    result_column, log_column = st.columns(2)
    if result_column.button(
        "查询选中评测结果",
        type="primary",
        use_container_width=True,
        disabled=submission_id is None,
    ):
        _open_submission(str(submission_id), "result")
    if log_column.button(
        "查询选中评测日志",
        use_container_width=True,
        disabled=submission_id is None,
    ):
        _open_submission(str(submission_id), "log")


def render_page() -> None:
    """Render the submissions module."""
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
        st.error("user_id 与 problem_id 至少需要提供一个。")
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
    st.caption(f"总数：{total} · 第 {current_page}/{max_page} 页")
    selected_submission_id = render_submission_table(rows)
    render_submission_selector(selected_submission_id)
