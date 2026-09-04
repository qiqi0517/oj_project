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
    """获取 submission 总体评测结果。"""
    status_code, body = get_submission(submission_id)
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        st.error("后端提交详情响应格式异常。")
        return None
    if data.get("status") not in {"pending", "success", "error"}:
        st.error("后端提交详情缺少有效的评测状态。")
        return None
    return data


def load_submission_log(submission_id: str) -> dict[str, Any] | None:
    """获取当前用户有权限查看的评测日志。"""
    status_code, body = get_submission_log(submission_id)
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        st.error("后端评测日志响应格式异常。")
        return None
    details = data.get("details")
    score = data.get("score")
    counts = data.get("counts")
    if (
        not isinstance(details, list)
        or not isinstance(score, int)
        or not isinstance(counts, int)
    ):
        st.error("后端评测日志缺少有效的 details、score 或 counts 字段。")
        return None
    return data


def _render_phase_info(title: str, info: Any, empty_message: str) -> None:
    st.markdown(f"### {title}")
    if not isinstance(info, dict):
        st.info(empty_message)
        return
    st.write(f"result: {info.get('result', '未知')}")
    message = info.get("message")
    if message:
        st.code(str(message), language=None)
    else:
        st.caption("没有附加信息。")


def render_submission_detail(submission: dict[str, Any]) -> None:
    """展示总体状态、分数、编译信息、运行信息和错误信息。"""
    submission_id = submission.get("submission_id", "未知")
    st.subheader(f"评测结果 · {submission_id}")
    status = str(submission.get("status", ""))
    render_submission_status(status)

    score_column, counts_column = st.columns(2)
    score = submission.get("score")
    counts = submission.get("counts")
    score_column.metric("score", score if score is not None else "等待评测")
    counts_column.metric("counts", counts if counts is not None else "等待评测")

    _render_phase_info(
        "compile_info",
        submission.get("compile_info"),
        "当前尚无编译信息；解释型语言通常不需要编译。",
    )
    _render_phase_info(
        "run_info",
        submission.get("run_info"),
        "当前尚无运行信息。",
    )

    st.markdown("### error_info")
    error_info = submission.get("error_info")
    if error_info:
        st.error(str(error_info))
    else:
        st.caption("无任务级错误。")


def render_submission_log(log_data: dict[str, Any]) -> None:
    """展示测试点 details、score 和 counts。"""
    st.markdown("### details")
    score_column, counts_column = st.columns(2)
    score_column.metric("score", log_data.get("score", 0))
    counts_column.metric("counts", log_data.get("counts", 0))
    details = log_data.get("details", [])
    render_testcase_details(
        [detail for detail in details if isinstance(detail, dict)]
        if isinstance(details, list)
        else []
    )


def render_pending_state(submission_id: str) -> None:
    """评测仍为 pending 时展示状态和重新查询入口。"""
    st.info(f"提交 {submission_id} 正在排队或评测中。")
    if st.button("重新查询评测状态", type="primary"):
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
    """提交详情页面入口。"""
    if not require_login():
        return

    _render_back_button()
    notice = st.session_state.pop(_NOTICE_KEY, None)
    if isinstance(notice, str):
        st.success(notice)

    submission_id = get_selected_submission()
    if not submission_id:
        st.error("没有选择要查看的评测。")
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
