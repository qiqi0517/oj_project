from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import get_submission, get_submission_log
    from ..session import get_selected_submission, set_selected_submission
    from ..ui import (
        render_submission_status,
        render_testcase_details,
        require_login,
        show_api_message,
    )
else:
    from api_client import get_submission, get_submission_log
    from session import get_selected_submission, set_selected_submission
    from ui import (
        render_submission_status,
        render_testcase_details,
        require_login,
        show_api_message,
    )


_PROBLEM_VIEW_KEY = "problem_page_view"
_SUBMISSION_VIEW_KEY = "submission_page_view"
_RETURN_KEY = "submission_return_view"
_DETAIL_MODE_KEY = "submission_detail_mode"
_NOTICE_KEY = "submission_notice"


def load_submission_detail(submission_id: str) -> dict[str, Any] | None:
    """Load a result through GET /api/submissions/{submission_id}."""
    status_code, body = get_submission(submission_id)
    if not show_api_message(status_code, body, show_success=False):
        return None
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应为评测对象。")
        return None
    if data.get("status") not in {"pending", "success", "error"}:
        st.error("API 响应格式无效：status 必须为 pending、success 或 error。")
        return None
    return data


def load_submission_log(submission_id: str) -> dict[str, Any] | None:
    """Load a judge log through GET /api/submissions/{submission_id}/log."""
    status_code, body = get_submission_log(submission_id)
    if not show_api_message(status_code, body, show_success=False):
        return None
    data = body.get("data")  # type: ignore
    if not isinstance(data, dict):
        st.error("API 响应格式无效：data 应为评测日志对象。")
        return None
    details = data.get("details")
    score = data.get("score")
    counts = data.get("counts")
    if (
        not isinstance(details, list)
        or not isinstance(score, int)
        or not isinstance(counts, int)
    ):
        st.error("API 响应格式无效：details、score 或 counts 的类型不正确。")
        return None
    return data


def _render_phase_info(title: str, info: Any, empty_message: str) -> None:
    st.markdown(f"### {title}")
    if not isinstance(info, dict):
        st.info(empty_message)
        return
    st.write(f"结果：{info.get('result', '未知')}")
    message = info.get("message")
    if message:
        st.code(str(message), language=None)
    else:
        st.caption("暂无附加 message。")


def render_submission_detail(submission: dict[str, Any]) -> None:
    """Render the submission result fields defined by the API."""
    submission_id = submission.get("submission_id", "未知")
    st.subheader(f"评测结果 · {submission_id}")
    status = str(submission.get("status", ""))
    render_submission_status(status)

    score_column, counts_column = st.columns(2)
    score = submission.get("score")
    counts = submission.get("counts")
    score_column.metric("得分", score if score is not None else "等待评测")
    counts_column.metric("测试点数", counts if counts is not None else "等待评测")

    _render_phase_info(
        "编译信息",
        submission.get("compile_info"),
        "暂无编译信息（解释型编程语言没有编译阶段）",
    )
    _render_phase_info(
        "运行信息",
        submission.get("run_info"),
        "暂无运行信息",
    )
    _render_phase_info(
        "错误信息",
        submission.get("error_info"),
        "暂无测评级错误信息",
    )


def render_submission_log(log_data: dict[str, Any]) -> None:
    """Render the details, score, and counts judge-log fields."""
    st.markdown("### 测试点明细")
    score_column, counts_column = st.columns(2)
    score_column.metric("得分", log_data.get("score", 0))
    counts_column.metric("测试点数", log_data.get("counts", 0))
    details = log_data.get("details", [])
    render_testcase_details(
        [detail for detail in details if isinstance(detail, dict)]
        if isinstance(details, list)
        else []
    )


def render_pending_state(submission_id: str) -> None:
    """Render a refresh action while status is pending."""
    st.info(f"评测 {submission_id} 正在排队或执行中。")
    if st.button("刷新评测结果", type="primary"):
        st.rerun()


def _render_back_button() -> None:
    return_view = st.session_state.get(_RETURN_KEY, "list")
    label = "← 返回题目详情" if return_view == "problem" else "← 返回评测列表"
    if not st.button(label):
        return

    st.session_state[_SUBMISSION_VIEW_KEY] = "list"
    if return_view == "problem":
        st.session_state[_PROBLEM_VIEW_KEY] = "detail"
    else:
        set_selected_submission(None)
    st.rerun()


def render_page() -> None:
    """Render either a submission result or its judge log."""
    if not require_login():
        return

    _render_back_button()
    notice = st.session_state.pop(_NOTICE_KEY, None)
    if isinstance(notice, str):
        st.success(notice)

    submission_id = get_selected_submission()
    if not submission_id:
        st.error("请先选择评测，再查询评测结果或评测日志。")
        return

    mode = st.session_state.get(_DETAIL_MODE_KEY, "result")
    if mode == "log":
        st.subheader(f"评测日志 · {submission_id}")
        log_data = load_submission_log(submission_id)
        if log_data is not None:
            render_submission_log(log_data)
        return

    submission = load_submission_detail(submission_id)
    if submission is None:
        return
    render_submission_detail(submission)
    if submission.get("status") == "pending":
        render_pending_state(submission_id)
