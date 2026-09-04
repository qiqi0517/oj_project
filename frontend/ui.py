from typing import Any

import streamlit as st


_STATUS_MESSAGES = {
    400: "请求参数有误，请检查填写内容。",
    401: "尚未登录或登录状态已失效，请重新登录。",
    403: "权限不足，或账号已被禁用。",
    404: "请求的资源不存在。",
    409: "资源状态冲突，请刷新后重试。",
    429: "操作过于频繁，请稍后再试。",
    500: "服务器内部错误，请稍后重试。",
}

_API_MESSAGE_TRANSLATIONS = {
    "success": "操作成功。",
    "add success": "题目新增成功。",
    "update success": "题目更新成功。",
    "delete success": "题目删除成功。",
    "login success": "登录成功。",
    "logout success": "退出登录成功。",
    "register success": "注册成功。",
    "role updated": "用户角色更新成功。",
    "language registered": "编程语言注册成功。",
    "rejudge started": "已开始重新评测。",
    "log visibility updated": "评测日志可见性更新成功。",
    "system reset successfully": "系统重置成功。",
    "validation error": "请求参数格式错误。",
    "invalid username or password": "用户名或密码错误。",
    "not authenticated": "尚未登录或登录状态已失效，请重新登录。",
    "user is banned": "账号已被禁用，无法执行此操作。",
    "permission denied": "当前用户没有权限执行此操作。",
    "problem not found": "题目不存在。",
    "language not found": "编程语言不存在。",
    "submission not found": "提交记录不存在。",
    "user not found": "用户不存在。",
    "problem already exists": "题目编号已存在。",
    "username already exists": "用户名已存在。",
    "problem id does not match path": "请求体中的题目编号与当前题目不一致。",
    "submission rate limit exceeded": "一分钟内最多提交 3 次，请稍后再试。",
    "page_size is required": "指定页码时必须同时提供每页数量。",
    "user_id or problem_id is required": "用户编号和题目编号至少填写一项。",
    "submission is still pending": "该提交仍在评测中，暂时不能重新评测。",
    "internal server error": "服务器内部错误，请稍后重试。",
}


def _display_message(status_code: int, message: str) -> str:
    translated = _API_MESSAGE_TRANSLATIONS.get(message)
    if translated is not None:
        return translated

    fallback = (
        "操作成功。"
        if 200 <= status_code < 300
        else _STATUS_MESSAGES.get(
            status_code,
            f"请求失败（HTTP {status_code}）。",
        )
    )
    if message:
        return f"{fallback}（服务端信息：{message}）"
    return fallback


def show_api_message(
    status_code: int | None,
    body: dict[str, Any] | None,
    *,
    success_message: str | None = None,
) -> bool:
    """
    根据 HTTP 状态码和 {code, msg, data} 显示提示。
    成功返回 True，失败返回 False。
    """
    if status_code is None:
        st.error("无法连接后端，请确认后端服务是否已启动。")
        return False

    if body is None:
        st.error("后端返回了无法解析的响应。")
        return False

    response_code = body.get("code")
    message = body.get("msg")

    if (
        not isinstance(response_code, int)
        or not isinstance(message, str)
        or "data" not in body
    ):
        st.error("后端响应格式异常，缺少有效的 code、msg 或 data 字段。")
        return False

    if response_code != status_code:
        st.error("后端响应格式异常：HTTP 状态码与响应 code 不一致。")
        return False

    if 200 <= status_code < 300:
        display_message = success_message or _display_message(status_code, message)
        st.success(display_message)
        return True

    st.error(_display_message(status_code, message))
    return False


def require_login() -> bool:
    """
    未登录时显示提示并返回 False。
    已登录返回 True。
    注意：只是前端体验控制，不能替代后端权限校验。
    """
    ...


def require_admin() -> bool:
    """
    非管理员时显示提示并返回 False。
    管理员返回 True。
    注意：真正权限仍以后端响应为准。
    """
    ...


def render_user_summary(user: dict[str, Any]) -> None:
    """统一展示用户基本信息。"""
    ...


def render_problem_summary(problem: dict[str, Any]) -> None:
    """展示题目简要信息。"""
    ...


def render_submission_status(status: str) -> None:
    """统一展示 pending / success / error 状态。"""
    ...


def render_testcase_details(details: list[dict[str, Any]]) -> None:
    """展示评测日志中的测试点详情。"""
    ...
