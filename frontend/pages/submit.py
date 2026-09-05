from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import create_submission, list_languages, list_problems
    from ..session import get_selected_problem, set_selected_submission
    from ..ui import require_login, show_api_message
else:
    from api_client import create_submission, list_languages, list_problems
    from session import get_selected_problem, set_selected_submission
    from ui import require_login, show_api_message


_PROBLEM_VIEW_KEY = "problem_page_view"
_SUBMISSION_VIEW_KEY = "submission_page_view"
_SUBMISSION_RETURN_KEY = "submission_return_view"
_SUBMISSION_DETAIL_MODE_KEY = "submission_detail_mode"
_NOTICE_KEY = "submission_notice"


def load_problem_options() -> list[dict[str, Any]]:
    """Load problem_id options through GET /api/problems/."""
    status_code, body = list_problems()
    if not show_api_message(status_code, body, show_success=False):
        return []
    data = body.get("data")  # type: ignore
    if not isinstance(data, list):
        st.error("API 响应格式无效：data 应为题目列表。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def load_language_options() -> list[str]:
    """Load language options through GET /api/languages/."""
    status_code, body = list_languages()
    if not show_api_message(status_code, body, show_success=False):
        return []
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict) or not isinstance(data.get("name"), list):
        st.error("API 响应格式无效：data.name 应为列表。")
        return []
    return [name for name in data["name"] if isinstance(name, str) and name]


def render_submission_form(
    problems: list[dict[str, Any]],
    languages: list[str],
) -> tuple[str, str, str] | None:
    """
    Return (problem_id, language, code) after form submission.
    """
    problem_labels = {
        f"{problem.get('id', '')} · {problem.get('title', '未命名题目')}": str(
            problem.get("id", "")
        )
        for problem in problems
        if isinstance(problem.get("id"), str) and problem.get("id")
    }
    if not problem_labels:
        st.info("暂无可提交的题目。")
        return None
    if not languages:
        st.info("后端当前未提供任何编程语言。")
        return None

    selected_problem_id = get_selected_problem()
    labels = list(problem_labels)
    selected_index = next(
        (
            index
            for index, label in enumerate(labels)
            if problem_labels[label] == selected_problem_id
        ),
        0,
    )

    with st.form("submission_form"):
        selected_label = st.selectbox(
            "题目",
            labels,
            index=selected_index,
            disabled=selected_problem_id in problem_labels.values(),
            key=f"submission_problem_{selected_problem_id or 'default'}",
        )
        language = st.selectbox("编程语言", languages)
        code = st.text_area(
            "源代码",
            height=360,
            placeholder="请输入完整源代码",
        )
        submitted = st.form_submit_button(
            "提交评测",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return None
    if not code.strip():
        st.error("code 为必填项。")
        return None
    return problem_labels[selected_label], language, code


def submit_code(
    problem_id: str,
    language: str,
    code: str,
) -> str | None:
    """Create a submission and return submission_id on success."""
    status_code, body = create_submission(problem_id, language, code)
    if not show_api_message(status_code, body):
        return None

    data = body.get("data") if body is not None else None
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应为评测对象。")
        return None
    submission_id = data.get("submission_id")
    status = data.get("status")
    if (
        not isinstance(submission_id, str)
        or not submission_id
        or status not in {"pending", "success", "error"}
    ):
        st.error("API 响应格式无效：submission_id 或 status 无效。")
        return None

    set_selected_submission(submission_id)
    return submission_id


def _open_created_submission(submission_id: str) -> None:
    st.session_state[_SUBMISSION_VIEW_KEY] = "detail"
    st.session_state[_SUBMISSION_RETURN_KEY] = "problem"
    st.session_state[_SUBMISSION_DETAIL_MODE_KEY] = "result"
    st.session_state[_PROBLEM_VIEW_KEY] = "submission_detail"
    st.session_state[_NOTICE_KEY] = f"评测 {submission_id} 已进入队列。"
    st.rerun()


def render_problem_submission(problem: dict[str, Any]) -> None:
    """在题目详情右侧渲染当前题目的代码提交面板。"""
    problem_id = problem.get("id")
    if not isinstance(problem_id, str) or not problem_id:
        st.error("当前题目没有有效的 problem_id。")
        return

    st.subheader("提交代码")
    st.caption(f"题目：{problem_id} · {problem.get('title', '未命名题目')}")
    languages = load_language_options()
    if not languages:
        st.info("后端当前未提供任何编程语言。")
        return

    with st.form(f"problem_submission_form_{problem_id}"):
        language = st.selectbox("编程语言", languages)
        code = st.text_area(
            "源代码",
            height=520,
            placeholder="请输入完整源代码",
            key=f"problem_submission_code_{problem_id}",
        )
        submitted = st.form_submit_button(
            "提交评测",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return
    if not code.strip():
        st.error("code 为必填项。")
        return
    submission_id = submit_code(problem_id, language, code)
    if submission_id is not None:
        _open_created_submission(submission_id)


def render_page() -> None:
    """Render the code submission page."""
    if not require_login():
        return

    st.subheader("提交代码")
    submission = render_submission_form(
        load_problem_options(),
        load_language_options(),
    )
    if submission is None:
        return

    submission_id = submit_code(*submission)
    if submission_id is None:
        return

    _open_created_submission(submission_id)
