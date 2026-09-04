from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import delete_problem, get_problem, list_problems
    from ..session import get_selected_problem, is_admin, set_selected_problem
    from ..ui import render_problem_summary, require_login, show_api_message
else:
    from api_client import delete_problem, get_problem, list_problems
    from session import get_selected_problem, is_admin, set_selected_problem
    from ui import render_problem_summary, require_login, show_api_message


_VIEW_KEY = "problem_page_view"
_NOTICE_KEY = "problem_notice"


def _open_view(view: str, problem_id: str | None = None) -> None:
    if problem_id is not None:
        set_selected_problem(problem_id)
    st.session_state[_VIEW_KEY] = view
    st.rerun()


def load_problem_list() -> list[dict[str, Any]]:
    """加载题目列表。"""
    status_code, body = list_problems()
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return []

    data = body.get("data")
    if not isinstance(data, list):
        st.error("后端题目列表响应格式异常。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def render_problem_list(problems: list[dict[str, Any]]) -> None:
    """展示所有题目的 id 和 title。"""
    if not problems:
        st.info("当前没有题目，可以先新增一道题目。")
        return

    rows = [
        {"题目 ID": problem.get("id", ""), "标题": problem.get("title", "")}
        for problem in problems
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    selectable = [
        problem
        for problem in problems
        if isinstance(problem.get("id"), str) and problem.get("id")
    ]
    if not selectable:
        return
    labels = {
        f"{problem['id']} · {problem.get('title', '未命名题目')}": problem["id"]
        for problem in selectable
    }
    selected_label = st.selectbox("选择要查看的题目", list(labels))
    if st.button("查看题目详情", type="primary", use_container_width=True):
        _open_view("detail", labels[selected_label])


def load_problem_detail(problem_id: str) -> dict[str, Any] | None:
    """加载题目详情。"""
    status_code, body = get_problem(problem_id)
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return None

    data = body.get("data")
    if not isinstance(data, dict):
        st.error("后端题目详情响应格式异常。")
        return None
    return data


def _render_samples(samples: Any) -> None:
    st.markdown("### 样例")
    if not isinstance(samples, list) or not samples:
        st.info("该题目没有可显示的样例。")
        return

    for index, sample in enumerate(samples, start=1):
        if not isinstance(sample, dict):
            continue
        st.markdown(f"**样例 {index}**")
        input_column, output_column = st.columns(2)
        with input_column:
            st.caption("输入")
            st.code(str(sample.get("input", "")), language=None)
        with output_column:
            st.caption("输出")
            st.code(str(sample.get("output", "")), language=None)


def render_problem_detail(problem: dict[str, Any]) -> None:
    """展示完整题面。"""
    render_problem_summary(problem)
    st.markdown("### 题目描述")
    st.markdown(str(problem.get("description", "")))
    st.markdown("### 输入说明")
    st.markdown(str(problem.get("input_description", "")))
    st.markdown("### 输出说明")
    st.markdown(str(problem.get("output_description", "")))
    _render_samples(problem.get("samples"))
    st.markdown("### 数据范围与约束")
    st.markdown(str(problem.get("constraints", "")))

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
    """展示进入编辑、提交以及管理员删除等操作入口。"""
    edit_column, submit_column = st.columns(2)
    if edit_column.button("编辑题目", use_container_width=True):
        _open_view("edit", problem_id)
    if submit_column.button("提交代码", type="primary", use_container_width=True):
        _open_view("submit", problem_id)

    if is_admin():
        confirm_and_delete_problem(problem_id)


def confirm_and_delete_problem(problem_id: str) -> None:
    """管理员删除题目。"""
    with st.expander("删除题目", expanded=False):
        st.warning("删除会同时移除相关测试点、提交和评测日志，且无法撤销。")
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
    if top_right.button("新增题目", type="primary", use_container_width=True):
        _open_view("create")
    render_problem_list(load_problem_list())


def _render_detail_page(problem_id: str) -> None:
    if st.button("← 返回题目列表"):
        _open_view("list")
    problem = load_problem_detail(problem_id)
    if problem is None:
        return
    render_problem_detail(problem)
    st.divider()
    render_problem_actions(problem_id)


def _render_submit_entry(problem_id: str) -> None:
    if st.button("← 返回题目详情"):
        _open_view("detail", problem_id)
    st.subheader(f"提交代码 · {problem_id}")
    st.info("提交入口已关联当前题目；代码与语言表单将在阶段 5 接入。")


def render_page() -> None:
    """题目页面入口。"""
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
        _render_submit_entry(problem_id)
    else:
        if view != "list":
            st.session_state[_VIEW_KEY] = "list"
        _render_list_page()
