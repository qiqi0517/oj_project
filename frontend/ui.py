from typing import Any

import streamlit as st

if __package__:
    from .session import is_admin, is_logged_in
else:
    from session import is_admin, is_logged_in


_STATUS_MESSAGES = {
    400: "请求参数无效，请检查提交的字段。",
    401: "需要登录或 Session 已过期，请重新登录。",
    403: "权限不足，或当前账号已被封禁。",
    404: "未找到请求的资源。",
    409: "资源状态冲突，请刷新后重试。",
    429: "请求过于频繁，请稍后重试。",
    500: "后端发生内部错误，请稍后重试。",
}

_API_MESSAGE_TRANSLATIONS = {
    "success": "请求成功。",
    "add success": "题目创建成功。",
    "update success": "题目更新成功。",
    "delete success": "题目删除成功。",
    "login success": "登录成功。",
    "logout success": "已退出登录。",
    "register success": "账号注册成功。",
    "role updated": "用户 role 更新成功。",
    "language registered": "language 注册成功。",
    "rejudge started": "已开始重新评测。",
    "log visibility updated": "评测日志可见性更新成功。",
    "system reset successfully": "系统重置完成。",
    "validation error": "请求字段校验失败。",
    "invalid username or password": "username 或 password 错误。",
    "not authenticated": "需要登录或 Session 已过期。",
    "user is banned": "当前账号已被封禁。",
    "permission denied": "当前用户无权执行此操作。",
    "problem not found": "未找到题目。",
    "language not found": "未找到 language。",
    "submission not found": "未找到评测记录。",
    "user not found": "未找到用户。",
    "problem already exists": "该 id 对应的题目已存在。",
    "username already exists": "该 username 已存在。",
    "language already exists": "该 language 已存在。",
    "problem id does not match path": (
        "请求体字段 id 必须与路径参数 problem_id 一致。"
    ),
    "submission rate limit exceeded": ("每分钟最多提交 3 次，请稍后重试。"),
    "page_size is required": "提供 page 时必须同时提供 page_size。",
    "user_id or problem_id is required": ("user_id 与 problem_id 至少需要提供一个。"),
    "submission is still pending": "该提交仍在等待评测。",
    "internal server error": "后端发生内部错误。",
}

_ROLE_LABELS = {
    "user": "普通用户",
    "admin": "管理员",
    "banned": "已封禁",
}
_DIFFICULTY_LABELS = {
    "easy": "简单",
    "medium": "中等",
    "hard": "困难",
}
_SUBMISSION_STATUS_LABELS = {
    "pending": "等待评测",
    "success": "评测完成",
    "error": "评测失败",
}


def _display_message(status_code: int, message: str) -> str:
    fallback = (
        "请求成功。"
        if 200 <= status_code < 300
        else _STATUS_MESSAGES.get(
            status_code,
            f"请求失败，HTTP 状态码为 {status_code}。",
        )
    )
    summary = _API_MESSAGE_TRANSLATIONS.get(message, fallback)
    details = f"HTTP {status_code}"
    if message:
        details += f"，msg: {message}"
    return f"{summary}（{details}）"


def show_api_message(
    status_code: int | None,
    body: dict[str, Any] | None,
    *,
    success_message: str | None = None,
    show_success: bool = True,
) -> bool:
    """Validate and display an API response; return whether it succeeded."""
    if status_code is None:
        st.error("无法连接后端，请确认 FastAPI 服务已经启动。")
        return False

    if body is None:
        st.error(f"后端返回了非 JSON 响应（HTTP {status_code}）。")
        return False

    response_code = body.get("code")
    message = body.get("msg")

    if (
        not isinstance(response_code, int)
        or not isinstance(message, str)
        or "data" not in body
    ):
        st.error("API 响应格式无效：应包含 code（int）、msg（str）和 data 字段。")
        return False

    if response_code != status_code:
        st.error(
            "API 响应格式无效：HTTP 状态码 "
            f"{status_code} 与 JSON code {response_code} 不一致。"
        )
        return False

    if not 200 <= status_code < 300:
        st.error(_display_message(status_code, message))
        return False

    if show_success:
        display_message = success_message or _display_message(status_code, message)
        st.success(display_message)
    return True


def require_login() -> bool:
    """Return whether a user is signed in; backend checks remain authoritative."""
    if is_logged_in():
        return True
    st.warning("请先登录后再访问此页面。")
    return False


def require_admin() -> bool:
    """Return whether the current user is an admin for navigation purposes."""
    if not require_login():
        return False
    if is_admin():
        return True
    st.error("此页面仅限 admin 访问。")
    return False


def get_selected_row_index(event: Any) -> int | None:
    """读取 Streamlit 表格的单行选择结果。"""
    if event is None:
        return None
    selection = getattr(event, "selection", None)
    if selection is None and isinstance(event, dict):
        selection = event.get("selection")
    rows = getattr(selection, "rows", None)
    if rows is None and isinstance(selection, dict):
        rows = selection.get("rows")
    if not isinstance(rows, list) or not rows:
        return None
    index = rows[0]
    return index if isinstance(index, int) and index >= 0 else None


def format_role(role: Any) -> str:
    value = str(role or "")
    return _ROLE_LABELS.get(value, value or "未知")


def format_difficulty(difficulty: Any) -> str:
    value = str(difficulty or "")
    return _DIFFICULTY_LABELS.get(value, value or "未设置")


def format_submission_status(status: Any) -> str:
    value = str(status or "")
    return _SUBMISSION_STATUS_LABELS.get(value, value or "未知")


def render_user_summary(user: dict[str, Any]) -> None:
    """Render the public user fields defined by the API."""
    st.subheader(str(user.get("username", "未知用户")))
    st.caption(f"用户编号：{user.get('user_id', '未提供')}")
    first, second, third = st.columns(3)
    first.metric("用户角色", format_role(user.get("role")))
    second.metric("提交次数", user.get("submit_count", 0))
    third.metric("通过题数", user.get("resolve_count", 0))
    st.write(f"注册时间：{user.get('join_time', '未提供')}")


def render_problem_summary(problem: dict[str, Any]) -> None:
    """Render the summary fields of a problem."""
    st.subheader(str(problem.get("title", "未命名题目")))
    st.caption(f"题目编号：{problem.get('id', '未提供')}")

    tags = problem.get("tags", [])
    if isinstance(tags, list) and tags:
        st.write("标签：" + "、".join(str(tag) for tag in tags))

    with st.container(key="problem_metadata"):
        first, second, third = st.columns(3)
        first.metric("难度", format_difficulty(problem.get("difficulty")))
        time_limit = problem.get("time_limit")
        memory_limit = problem.get("memory_limit")
        second.metric(
            "时间限制",
            f"{time_limit} 秒" if time_limit is not None else "默认",
        )
        third.metric(
            "空间限制",
            f"{memory_limit} MB" if memory_limit is not None else "默认",
        )


def render_submission_status(status: str) -> None:
    """Render one of the API submission states: pending, success, or error."""
    if status == "pending":
        st.info("评测状态：等待评测")
    elif status == "success":
        st.success("评测状态：评测完成")
    elif status == "error":
        st.error("评测状态：评测失败")
    else:
        st.warning(f"评测状态：{status or '未知'}")


def render_testcase_details(details: list[dict[str, Any]]) -> None:
    """Render the API judge-log details fields."""
    if not details:
        st.info("暂无 testcase 评测明细。")
        return
    rows = [
        {
            "测试点": detail.get("id", ""),
            "结果": detail.get("result", ""),
            "用时": detail.get("time", 0),
            "内存": detail.get("memory", 0),
        }
        for detail in details
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
