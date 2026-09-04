from typing import Any

import requests

if __package__:
    from .config import API_BASE_URL, REQUEST_TIMEOUT
    from .session import get_api_session
else:
    from config import API_BASE_URL, REQUEST_TIMEOUT
    from session import get_api_session

ApiResponse = dict[str, Any]


# 通用请求

def request_api(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """
    返回：
    - HTTP 状态码；网络连接失败时为 None
    - 后端 JSON；无法获得合法 JSON 时为 None
    """
    url = f"{API_BASE_URL}/{path.lstrip('/')}"

    try:
        response = get_api_session().request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException:
        return None, None

    try:
        body = response.json()
    except (requests.JSONDecodeError, ValueError):
        return response.status_code, None

    if not isinstance(body, dict):
        return response.status_code, None

    return response.status_code, body


# 用户接口

def login(
    username: str,
    password: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/auth/login"""
    ...


def logout() -> tuple[int | None, ApiResponse | None]:
    """POST /api/auth/logout"""
    ...


def register_user(
    username: str,
    password: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/users/"""
    ...


def get_user(
    user_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/users/{user_id}"""
    ...


def list_users(
    *,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/users/"""
    ...


def update_user_role(
    user_id: str,
    role: str,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/users/{user_id}/role"""
    ...


# 题目接口

def list_problems() -> tuple[int | None, ApiResponse | None]:
    """GET /api/problems/"""
    ...


def get_problem(
    problem_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/problems/{problem_id}"""
    ...


def create_problem(
    problem_data: dict[str, Any],
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/problems/"""
    ...


def update_problem(
    problem_id: str,
    problem_data: dict[str, Any],
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/problems/{problem_id}"""
    ...


def delete_problem(
    problem_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """DELETE /api/problems/{problem_id}"""
    ...


# 语言接口

def list_languages() -> tuple[int | None, ApiResponse | None]:
    """GET /api/languages/"""
    ...


# 提交与评测接口

def create_submission(
    problem_id: str,
    language: str,
    code: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/submissions/"""
    ...


def list_submissions(
    *,
    user_id: str | None = None,
    problem_id: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/"""
    ...


def get_submission(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/{submission_id}"""
    ...


def get_submission_log(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/{submission_id}/log"""
    ...

def rejudge_submission(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/submissions/{submission_id}/rejudge"""
    ...


def update_log_visibility(
    problem_id: str,
    public_cases: bool,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/problems/{problem_id}/log_visibility"""
    ...


def list_log_access(
    *,
    user_id: str | None = None,
    problem_id: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/logs/access/"""
    ...
