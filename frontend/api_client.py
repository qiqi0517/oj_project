from typing import Any

import requests

if __package__:
    from .config import API_BASE_URL, REQUEST_TIMEOUT
    from .session import clear_current_user, get_api_session
else:
    from config import API_BASE_URL, REQUEST_TIMEOUT
    from session import clear_current_user, get_api_session

ApiResponse = dict[str, Any]


# Shared request handling


def request_api(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """
    Return the HTTP status and decoded API object.

    A missing status means the request could not reach the backend. A missing
    body with a status means the backend returned a non-JSON response.
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

    if response.status_code == 401:
        clear_current_user()

    try:
        body = response.json()
    except (requests.JSONDecodeError, ValueError):
        return response.status_code, None

    if not isinstance(body, dict):
        return response.status_code, None

    if response.status_code == 403 and body.get("msg") == "user is banned":
        clear_current_user()

    return response.status_code, body


# User API


def login(
    username: str,
    password: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/auth/login"""
    return request_api(
        "POST",
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def logout() -> tuple[int | None, ApiResponse | None]:
    """POST /api/auth/logout"""
    return request_api("POST", "/api/auth/logout")


def register_user(
    username: str,
    password: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/users/"""
    return request_api(
        "POST",
        "/api/users/",
        json={"username": username, "password": password},
    )


def get_user(
    user_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/users/{user_id}"""
    return request_api("GET", f"/api/users/{user_id}")


def list_users(
    *,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/users/"""
    params = {
        key: value
        for key, value in {"page": page, "page_size": page_size}.items()
        if value is not None
    }
    return request_api("GET", "/api/users/", params=params or None)


def update_user_role(
    user_id: str,
    role: str,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/users/{user_id}/role"""
    return request_api(
        "PUT",
        f"/api/users/{user_id}/role",
        json={"role": role},
    )


# Problem API


def list_problems() -> tuple[int | None, ApiResponse | None]:
    """GET /api/problems/"""
    return request_api("GET", "/api/problems/")


def get_problem(
    problem_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/problems/{problem_id}"""
    return request_api("GET", f"/api/problems/{problem_id}")


def create_problem(
    problem_data: dict[str, Any],
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/problems/"""
    return request_api("POST", "/api/problems/", json=problem_data)


def update_problem(
    problem_id: str,
    problem_data: dict[str, Any],
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/problems/{problem_id}"""
    return request_api(
        "PUT",
        f"/api/problems/{problem_id}",
        json=problem_data,
    )


def delete_problem(
    problem_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """DELETE /api/problems/{problem_id}"""
    return request_api("DELETE", f"/api/problems/{problem_id}")


# Language API


def list_languages() -> tuple[int | None, ApiResponse | None]:
    """GET /api/languages/"""
    return request_api("GET", "/api/languages/")


# Submission and judging API


def create_submission(
    problem_id: str,
    language: str,
    code: str,
) -> tuple[int | None, ApiResponse | None]:
    """POST /api/submissions/"""
    return request_api(
        "POST",
        "/api/submissions/",
        json={
            "problem_id": problem_id,
            "language": language,
            "code": code,
        },
    )


def list_submissions(
    *,
    user_id: str | None = None,
    problem_id: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/"""
    params = {
        key: value
        for key, value in {
            "user_id": user_id,
            "problem_id": problem_id,
            "status": status,
            "page": page,
            "page_size": page_size,
        }.items()
        if value is not None
    }
    return request_api("GET", "/api/submissions/", params=params or None)


def get_submission(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/{submission_id}"""
    return request_api("GET", f"/api/submissions/{submission_id}")


def get_submission_log(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/submissions/{submission_id}/log"""
    return request_api("GET", f"/api/submissions/{submission_id}/log")


def rejudge_submission(
    submission_id: str,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/submissions/{submission_id}/rejudge"""
    return request_api("PUT", f"/api/submissions/{submission_id}/rejudge")


def update_log_visibility(
    problem_id: str,
    public_cases: bool,
) -> tuple[int | None, ApiResponse | None]:
    """PUT /api/problems/{problem_id}/log_visibility"""
    return request_api(
        "PUT",
        f"/api/problems/{problem_id}/log_visibility",
        json={"public_cases": public_cases},
    )


def list_log_access(
    *,
    user_id: str | None = None,
    problem_id: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int | None, ApiResponse | None]:
    """GET /api/logs/access/"""
    params = {
        key: value
        for key, value in {
            "user_id": user_id,
            "problem_id": problem_id,
            "page": page,
            "page_size": page_size,
        }.items()
        if value is not None
    }
    return request_api("GET", "/api/logs/access/", params=params or None)
