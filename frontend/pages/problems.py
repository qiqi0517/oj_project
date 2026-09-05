from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import delete_problem, get_problem, list_problems
    from ..session import get_selected_problem, is_admin, set_selected_problem
    from ..ui import (
        get_selected_row_index,
        render_problem_summary,
        require_login,
        show_api_message,
    )
else:
    from api_client import delete_problem, get_problem, list_problems
    from session import get_selected_problem, is_admin, set_selected_problem
    from ui import (
        get_selected_row_index,
        render_problem_summary,
        require_login,
        show_api_message,
    )


_VIEW_KEY = "problem_page_view"
_NOTICE_KEY = "problem_notice"


def _open_view(view: str, problem_id: str | None = None) -> None:
    if problem_id is not None:
        set_selected_problem(problem_id)
    st.session_state[_VIEW_KEY] = view
    st.rerun()


def load_problem_list() -> list[dict[str, Any]]:
    """Load problems through GET /api/problems/."""
    status_code, body = list_problems()
    if not show_api_message(status_code, body, show_success=False):
        return []

    data = body.get("data")  # type: ignore
    if not isinstance(data, list):
        st.error("API 响应格式无效：data 应为题目列表。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def render_problem_list(problems: list[dict[str, Any]]) -> None:
    """Render the id and title fields returned by the problem-list API."""
    if not problems:
        st.info("题库中暂无题目，可以先创建一道题目。")
        return

    rows = [
        {
            "题目编号": problem.get("id", ""),
            "题目名称": problem.get("title", ""),
        }
        for problem in problems
    ]
    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="problem_list_table",
    )
    selected_index = get_selected_row_index(event)
    selected_id = None
    if selected_index is not None and selected_index < len(problems):
        candidate = problems[selected_index].get("id")
        if isinstance(candidate, str) and candidate:
            selected_id = candidate
    st.caption("请在列表左侧选中一条题目记录。")
    if st.button(
        "查看选中题目",
        type="primary",
        use_container_width=True,
        disabled=selected_id is None,
    ):
        _open_view("detail", selected_id)


def load_problem_detail(problem_id: str) -> dict[str, Any] | None:
    """Load a problem through GET /api/problems/{problem_id}."""
    status_code, body = get_problem(problem_id)
    if not show_api_message(status_code, body, show_success=False):
        return None

    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应包含题目对象。")
        return None
    return data


def _render_io_cases(field_name: str, cases: Any) -> None:
    """展示 API 中 samples 或 testcases 的 input/output 字段。"""
    display_name = "样例" if field_name == "samples" else "测试点"
    st.markdown(f"### {display_name}")
    if not isinstance(cases, list) or not cases:
        st.info(f"该题目暂无{display_name}。")
        return

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            continue
        item_name = "样例" if field_name == "samples" else "测试点"
        st.markdown(f"**{item_name} {index}**")
        input_column, output_column = st.columns(2)
        with input_column:
            st.caption("输入")
            st.code(str(case.get("input", "")), language=None)
        with output_column:
            st.caption("输出")
            st.code(str(case.get("output", "")), language=None)


def render_problem_detail(problem: dict[str, Any]) -> None:
    """Render all problem fields returned by the API."""
    render_problem_summary(problem)
    st.markdown("### 题目描述")
    st.markdown(str(problem.get("description", "")))
    st.markdown("### 输入说明")
    st.markdown(str(problem.get("input_description", "")))
    st.markdown("### 输出说明")
    st.markdown(str(problem.get("output_description", "")))
    _render_io_cases("samples", problem.get("samples"))
    st.markdown("### 数据范围")
    st.markdown(str(problem.get("constraints", "")))
    with st.expander("测试点", expanded=False):
        _render_io_cases("testcases", problem.get("testcases"))

    hint = problem.get("hint")
    if hint:
        st.markdown("### 提示")
        st.markdown(str(hint))
    source = problem.get("source")
    author = problem.get("author")
    if source or author:
        st.caption(
            " · ".join(
                part
                for part in (
                    f"来源：{source}" if source else "",
                    f"作者：{author}" if author else "",
                )
                if part
            )
        )


def render_problem_actions(problem_id: str) -> None:
    """Render edit and admin-only delete actions."""
    if st.button("编辑题目", use_container_width=True):
        _open_view("edit", problem_id)

    if is_admin():
        confirm_and_delete_problem(problem_id)


def confirm_and_delete_problem(problem_id: str) -> None:
    """Delete a problem through the admin-only API endpoint."""
    with st.expander("删除题目", expanded=False):
        st.warning(
            "删除题目也会删除关联的 testcases、评测记录、评测日志和访问日志，"
            "且无法撤销。"
        )
        confirmed = st.checkbox(
            f"确认删除题目 {problem_id}",
            key=f"confirm_delete_problem_{problem_id}",
        )
        if not st.button(
            "永久删除",
            disabled=not confirmed,
            key=f"delete_problem_{problem_id}",
        ):
            return

        status_code, body = delete_problem(problem_id)
        if not show_api_message(status_code, body):
            return
        set_selected_problem(None)
        st.session_state[_VIEW_KEY] = "list"
        st.session_state[_NOTICE_KEY] = f"题目 {problem_id} 已删除。"
        st.rerun()


def _render_list_page() -> None:
    top_left, top_right = st.columns([3, 1])
    top_left.subheader("题目列表")
    if top_right.button("创建题目", type="primary", use_container_width=True):
        _open_view("create")
    render_problem_list(load_problem_list())


def _render_detail_page(problem_id: str) -> None:
    if st.button("← 返回题目列表"):
        _open_view("list")
    problem = load_problem_detail(problem_id)
    if problem is None:
        return
    detail_column, submission_column = st.columns(2, gap="large")
    with detail_column:
        render_problem_detail(problem)
        st.divider()
        render_problem_actions(problem_id)
    with submission_column:
        if __package__ == "frontend.pages":
            from . import submit
        else:
            from pages import submit
        submit.render_problem_submission(problem)


def _render_submission_detail() -> None:
    if __package__ == "frontend.pages":
        from . import submission_detail
    else:
        from pages import submission_detail
    submission_detail.render_page()


def render_page() -> None:
    """Render the problems module."""
    if not require_login():
        return

    notice = st.session_state.pop(_NOTICE_KEY, None)
    if isinstance(notice, str):
        st.success(notice)

    view = str(st.session_state.get(_VIEW_KEY, "list"))
    if view in {"create", "edit"}:
        if st.button("返回题目列表"):
            _open_view("list")
        if __package__ == "frontend.pages":
            from . import problem_editor
        else:
            from pages import problem_editor
        problem_editor.render_page()
        return

    problem_id = get_selected_problem()
    if view == "detail" and problem_id:
        _render_detail_page(problem_id)
    elif view == "submit" and problem_id:
        st.session_state[_VIEW_KEY] = "detail"
        st.rerun()
    elif view == "submission_detail":
        _render_submission_detail()
    else:
        if view != "list":
            st.session_state[_VIEW_KEY] = "list"
        _render_list_page()
