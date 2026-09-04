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
    """获取可提交题目。"""
    status_code, body = list_problems()
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return []
    data = body.get("data")
    if not isinstance(data, list):
        st.error("后端题目列表响应格式异常。")
        return []
    return [problem for problem in data if isinstance(problem, dict)]


def load_language_options() -> list[str]:
    """从 GET /api/languages/ 获取支持语言。"""
    status_code, body = list_languages()
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return []
    data = body.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("name"), list):
        st.error("后端语言列表响应格式异常。")
        return []
    return [name for name in data["name"] if isinstance(name, str) and name]


def render_submission_form(
    problems: list[dict[str, Any]],
    languages: list[str],
) -> tuple[str, str, str] | None:
    """
    返回：
    (problem_id, language, code)
    未提交时返回 None。
    """
    problem_labels = {
        f"{problem.get('id', '')} · {problem.get('title', '未命名题目')}": str(
            problem.get("id", "")
        )
        for problem in problems
        if isinstance(problem.get("id"), str) and problem.get("id")
    }
    if not problem_labels:
        st.info("当前没有可提交的题目。")
        return None
    if not languages:
        st.info("后端当前没有可用的编程语言。")
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
            "problem_id",
            labels,
            index=selected_index,
            disabled=selected_problem_id in problem_labels.values(),
            key=f"submission_problem_{selected_problem_id or 'default'}",
        )
        language = st.selectbox("language", languages)
        code = st.text_area(
            "code",
            height=360,
            placeholder="在这里输入完整代码……",
        )
        submitted = st.form_submit_button(
            "提交评测",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return None
    if not code.strip():
        st.error("源代码不能为空。")
        return None
    return problem_labels[selected_label], language, code


def submit_code(
    problem_id: str,
    language: str,
    code: str,
) -> str | None:
    """提交代码，成功时返回 submission_id。"""
    status_code, body = create_submission(problem_id, language, code)
    if not show_api_message(
        status_code,
        body,
        success_message="提交成功，评测任务已创建。",
    ):
        return None

    data = body.get("data") if body is not None else None
    if not isinstance(data, dict):
        st.error("后端提交响应格式异常。")
        return None
    submission_id = data.get("submission_id")
    status = data.get("status")
    if (
        not isinstance(submission_id, str)
        or not submission_id
        or status not in {"pending", "success", "error"}
    ):
        st.error("后端提交响应缺少有效的 submission_id 或 status。")
        return None

    set_selected_submission(submission_id)
    return submission_id


def render_page() -> None:
    """代码提交页面入口。"""
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

    st.session_state[_SUBMISSION_VIEW_KEY] = "detail"
    st.session_state[_SUBMISSION_RETURN_KEY] = "problem"
    st.session_state[_SUBMISSION_DETAIL_MODE_KEY] = "result"
    st.session_state[_PROBLEM_VIEW_KEY] = "submission_detail"
    st.session_state[_NOTICE_KEY] = f"提交 {submission_id} 已进入评测队列。"
    st.rerun()
