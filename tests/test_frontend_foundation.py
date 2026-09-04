import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from frontend import api_client
from frontend import app as frontend_app
from frontend import session as frontend_session
from frontend import ui
from frontend.pages import auth, problem_editor, problems, profile, users


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class StubResponse:
    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self._body = body

    def json(self) -> Any:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class StubSession:
    def __init__(self, response: StubResponse | Exception) -> None:
        self.response = response
        self.request_kwargs: dict[str, Any] | None = None

    def request(self, **kwargs: Any) -> StubResponse:
        self.request_kwargs = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_session_state_is_initialized_once(monkeypatch: Any) -> None:
    state: dict[str, Any] = {}
    monkeypatch.setattr(frontend_session.st, "session_state", state)

    frontend_session.init_session_state()
    api_session = frontend_session.get_api_session()
    frontend_session.init_session_state()

    assert frontend_session.get_api_session() is api_session
    assert frontend_session.get_current_user() is None
    assert frontend_session.get_selected_problem() is None
    assert frontend_session.get_selected_submission() is None


def test_session_helpers_manage_current_values(monkeypatch: Any) -> None:
    state: dict[str, Any] = {}
    monkeypatch.setattr(frontend_session.st, "session_state", state)

    user = {"user_id": "u1", "username": "admin", "role": "admin"}
    frontend_session.set_current_user(user)
    frontend_session.set_selected_problem("p1")
    frontend_session.set_selected_submission("s1")

    assert frontend_session.is_logged_in()
    assert frontend_session.is_admin()
    assert frontend_session.get_current_user() == user
    assert frontend_session.get_selected_problem() == "p1"
    assert frontend_session.get_selected_submission() == "s1"

    frontend_session.clear_current_user()
    assert not frontend_session.is_logged_in()
    assert not frontend_session.is_admin()
    assert frontend_session.get_selected_problem() is None
    assert frontend_session.get_selected_submission() is None
    assert not frontend_session.get_api_session().cookies


def test_request_api_uses_shared_session(monkeypatch: Any) -> None:
    stub_session = StubSession(
        StubResponse(200, {"code": 200, "msg": "success", "data": {}})
    )
    monkeypatch.setattr(api_client, "get_api_session", lambda: stub_session)
    monkeypatch.setattr(api_client, "API_BASE_URL", "http://api.example.test")

    status_code, body = api_client.request_api(
        "get",
        "/api/health",
        params={"verbose": True},
    )

    assert status_code == 200
    assert body == {"code": 200, "msg": "success", "data": {}}
    assert stub_session.request_kwargs == {
        "method": "GET",
        "url": "http://api.example.test/api/health",
        "params": {"verbose": True},
        "json": None,
        "timeout": api_client.REQUEST_TIMEOUT,
    }


def test_request_api_handles_network_and_json_errors(monkeypatch: Any) -> None:
    network_error_session = StubSession(requests.ConnectionError("offline"))
    monkeypatch.setattr(
        api_client,
        "get_api_session",
        lambda: network_error_session,
    )
    assert api_client.request_api("GET", "/api/health") == (None, None)

    invalid_json_session = StubSession(StubResponse(502, ValueError("not json")))
    monkeypatch.setattr(
        api_client,
        "get_api_session",
        lambda: invalid_json_session,
    )
    assert api_client.request_api("GET", "/api/health") == (502, None)


def test_request_api_discards_stale_or_banned_frontend_identity(
    monkeypatch: Any,
) -> None:
    cleared: list[bool] = []
    responses = iter(
        [
            StubResponse(401, {"code": 401, "msg": "not authenticated", "data": None}),
            StubResponse(403, {"code": 403, "msg": "user is banned", "data": None}),
        ]
    )

    class SequentialSession:
        cookies = requests.cookies.RequestsCookieJar()

        def request(self, **_kwargs: Any) -> StubResponse:
            return next(responses)

    monkeypatch.setattr(api_client, "get_api_session", SequentialSession)
    monkeypatch.setattr(api_client, "clear_current_user", lambda: cleared.append(True))

    api_client.request_api("GET", "/api/problems/")
    api_client.request_api("GET", "/api/problems/")

    assert cleared == [True, True]


def test_login_and_logout_use_documented_api_contract(monkeypatch: Any) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_request_api(
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        calls.append((method, path, kwargs))
        return 200, {"code": 200, "msg": "success", "data": None}

    monkeypatch.setattr(api_client, "request_api", fake_request_api)

    api_client.login("alice", "secret123")
    api_client.logout()

    assert calls == [
        (
            "POST",
            "/api/auth/login",
            {"json": {"username": "alice", "password": "secret123"}},
        ),
        ("POST", "/api/auth/logout", {}),
    ]


def test_user_helpers_use_documented_api_contract(monkeypatch: Any) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_request_api(
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        calls.append((method, path, kwargs))
        return 200, {"code": 200, "msg": "success", "data": None}

    monkeypatch.setattr(api_client, "request_api", fake_request_api)

    api_client.register_user("alice", "secret123")
    api_client.get_user("u1")
    api_client.list_users(page=2, page_size=10)
    api_client.update_user_role("u1", "banned")

    assert calls == [
        (
            "POST",
            "/api/users/",
            {"json": {"username": "alice", "password": "secret123"}},
        ),
        ("GET", "/api/users/u1", {}),
        ("GET", "/api/users/", {"params": {"page": 2, "page_size": 10}}),
        ("PUT", "/api/users/u1/role", {"json": {"role": "banned"}}),
    ]


def test_problem_helpers_use_documented_api_contract(monkeypatch: Any) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    problem_data = {"id": "P1", "title": "A+B"}

    def fake_request_api(
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        calls.append((method, path, kwargs))
        return 200, {"code": 200, "msg": "success", "data": None}

    monkeypatch.setattr(api_client, "request_api", fake_request_api)

    api_client.list_problems()
    api_client.get_problem("P1")
    api_client.create_problem(problem_data)
    api_client.update_problem("P1", problem_data)
    api_client.delete_problem("P1")

    assert calls == [
        ("GET", "/api/problems/", {}),
        ("GET", "/api/problems/P1", {}),
        ("POST", "/api/problems/", {"json": problem_data}),
        ("PUT", "/api/problems/P1", {"json": problem_data}),
        ("DELETE", "/api/problems/P1", {}),
    ]


def test_login_response_requires_complete_user_identity() -> None:
    body = {
        "code": 200,
        "msg": "login success",
        "data": {"user_id": "u1", "username": "alice", "role": "user"},
    }

    assert auth._login_user_from_response(200, body) == body["data"]
    assert auth._login_user_from_response(401, body) is None
    assert auth._login_user_from_response(
        200,
        {"code": 200, "msg": "login success", "data": {"username": "alice"}},
    ) is None


def test_show_api_message_reports_success_and_failures(monkeypatch: Any) -> None:
    successes: list[str] = []
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "success", successes.append)
    monkeypatch.setattr(ui.st, "error", errors.append)

    assert ui.show_api_message(
        200,
        {"code": 200, "msg": "success", "data": None},
        success_message="保存成功。",
    )
    assert not ui.show_api_message(None, None)
    assert not ui.show_api_message(
        403,
        {"code": 403, "msg": "user is banned", "data": None},
    )

    assert successes == ["保存成功。"]
    assert errors == [
        "无法连接后端，请确认后端服务是否已启动。",
        "账号已被禁用，无法执行此操作。",
    ]


def test_show_api_message_covers_required_status_codes(monkeypatch: Any) -> None:
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "error", errors.append)

    expected_messages = {
        400: "请求参数有误，请检查填写内容。",
        401: "尚未登录或登录状态已失效，请重新登录。",
        403: "权限不足，或账号已被禁用。",
        404: "请求的资源不存在。",
        409: "资源状态冲突，请刷新后重试。",
        429: "操作过于频繁，请稍后再试。",
        500: "服务器内部错误，请稍后重试。",
    }
    for status_code, expected in expected_messages.items():
        assert not ui.show_api_message(
            status_code,
            {"code": status_code, "msg": "", "data": None},
        )
        assert errors[-1] == expected


def test_show_api_message_rejects_invalid_response_contract(monkeypatch: Any) -> None:
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "error", errors.append)

    assert not ui.show_api_message(200, {"code": 400, "msg": "error", "data": None})
    assert not ui.show_api_message(200, {"code": 200, "msg": "success"})

    assert errors == [
        "后端响应格式异常：HTTP 状态码与响应 code 不一致。",
        "后端响应格式异常，缺少有效的 code、msg 或 data 字段。",
    ]


def test_permission_guards_follow_current_session(monkeypatch: Any) -> None:
    warnings: list[str] = []
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "warning", warnings.append)
    monkeypatch.setattr(ui.st, "error", errors.append)

    monkeypatch.setattr(ui, "is_logged_in", lambda: False)
    assert not ui.require_login()

    monkeypatch.setattr(ui, "is_logged_in", lambda: True)
    monkeypatch.setattr(ui, "is_admin", lambda: False)
    assert not ui.require_admin()

    monkeypatch.setattr(ui, "is_admin", lambda: True)
    assert ui.require_admin()
    assert warnings == ["请先登录后再访问此页面。"]
    assert errors == ["此页面仅限管理员访问。"]


def test_profile_refreshes_session_from_backend(monkeypatch: Any) -> None:
    latest_user = {
        "user_id": "u1",
        "username": "alice",
        "role": "admin",
        "join_time": "2026-09-04",
        "submit_count": 4,
        "resolve_count": 2,
    }
    saved_users: list[dict[str, Any]] = []
    monkeypatch.setattr(
        profile,
        "get_current_user",
        lambda: {"user_id": "u1", "username": "alice", "role": "user"},
    )
    monkeypatch.setattr(
        profile,
        "get_user",
        lambda user_id: (
            200,
            {"code": 200, "msg": "success", "data": latest_user},
        ),
    )
    monkeypatch.setattr(profile, "set_current_user", saved_users.append)

    assert profile.load_current_user_profile() == latest_user
    assert saved_users == [latest_user]


def test_profile_page_contains_logout_action(monkeypatch: Any) -> None:
    rendered: list[str] = []
    monkeypatch.setattr(profile, "require_login", lambda: True)
    monkeypatch.setattr(profile, "load_current_user_profile", lambda: {"user_id": "u1"})
    monkeypatch.setattr(profile, "render_profile", lambda _user: rendered.append("profile"))
    monkeypatch.setattr(profile.st, "divider", lambda: None)
    monkeypatch.setattr(profile.st, "subheader", lambda _message: None)
    monkeypatch.setattr(
        profile,
        "render_logout_button",
        lambda: rendered.append("logout"),
    )

    profile.render_page()

    assert rendered == ["profile", "logout"]


def test_user_list_loader_validates_documented_response(monkeypatch: Any) -> None:
    listed_users = [{"user_id": "u1", "username": "alice", "role": "user"}]
    monkeypatch.setattr(
        users,
        "list_users",
        lambda **_kwargs: (
            200,
            {
                "code": 200,
                "msg": "success",
                "data": {"total": 1, "users": listed_users},
            },
        ),
    )

    assert users.load_users(1, 10) == (1, listed_users)


def test_problem_form_validation_covers_required_shapes_and_limits() -> None:
    valid_problem = {
        "id": "P1",
        "title": "A+B",
        "description": "Add two numbers.",
        "input_description": "Two integers.",
        "output_description": "Their sum.",
        "samples": [{"input": "1 2", "output": "3"}],
        "constraints": "Integers.",
        "testcases": [{"input": "2 3", "output": "5"}],
        "tags": ["math"],
        "time_limit": None,
        "memory_limit": 128,
    }

    assert problem_editor.validate_problem_form(valid_problem) == []

    invalid_problem = valid_problem | {
        "title": " ",
        "samples": [],
        "testcases": [{"input": 1, "output": "1"}],
        "time_limit": 0,
        "memory_limit": 1.5,
        "tags": "math",
    }
    errors = problem_editor.validate_problem_form(invalid_problem)
    assert "标题不能为空。" in errors
    assert "至少需要填写一组样例。" in errors
    assert "第 1 组测试点必须包含字符串 input 和 output。" in errors
    assert "时间限制必须大于 0。" in errors
    assert "内存限制必须是大于 0 的整数。" in errors
    assert "标签必须是字符串列表。" in errors


def test_new_problem_limits_are_editable_and_empty_by_default(
    monkeypatch: Any,
) -> None:
    number_inputs: list[tuple[str, dict[str, Any]]] = []

    class FormContext:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_args: Any) -> None:
            return None

    monkeypatch.setattr(problem_editor.st, "form", lambda _key: FormContext())
    monkeypatch.setattr(
        problem_editor.st,
        "text_input",
        lambda _label, value="", **_kwargs: value,
    )
    monkeypatch.setattr(
        problem_editor.st,
        "text_area",
        lambda _label, value="", **_kwargs: value,
    )
    monkeypatch.setattr(problem_editor.st, "markdown", lambda _message: None)
    monkeypatch.setattr(problem_editor.st, "caption", lambda _message: None)
    monkeypatch.setattr(
        problem_editor.st,
        "data_editor",
        lambda rows, **_kwargs: rows,
    )
    monkeypatch.setattr(
        problem_editor.st,
        "checkbox",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("limit checkboxes must not be rendered")
        ),
    )

    def fake_number_input(label: str, **kwargs: Any) -> None:
        number_inputs.append((label, kwargs))
        return None

    monkeypatch.setattr(problem_editor.st, "number_input", fake_number_input)
    monkeypatch.setattr(
        problem_editor.st,
        "form_submit_button",
        lambda *_args, **_kwargs: False,
    )

    assert problem_editor.render_problem_form() is None
    assert [label for label, _kwargs in number_inputs] == [
        "时间限制（秒）",
        "内存限制（MB）",
    ]
    assert all(kwargs["value"] is None for _label, kwargs in number_inputs)
    assert all("disabled" not in kwargs for _label, kwargs in number_inputs)


def test_problem_loaders_validate_documented_responses(monkeypatch: Any) -> None:
    problem_list = [{"id": "P1", "title": "A+B"}]
    problem_detail = problem_list[0] | {
        "description": "Add.",
        "samples": [{"input": "1 2", "output": "3"}],
        "testcases": [{"input": "2 3", "output": "5"}],
    }
    monkeypatch.setattr(
        problems,
        "list_problems",
        lambda: (200, {"code": 200, "msg": "success", "data": problem_list}),
    )
    monkeypatch.setattr(
        problems,
        "get_problem",
        lambda problem_id: (
            200,
            {"code": 200, "msg": "success", "data": problem_detail},
        ),
    )

    assert problems.load_problem_list() == problem_list
    assert problems.load_problem_detail("P1") == problem_detail


def test_problem_detail_actions_include_submit_entry(monkeypatch: Any) -> None:
    opened: list[tuple[str, str | None]] = []

    class ActionColumn:
        def __init__(self, clicked_label: str) -> None:
            self.clicked_label = clicked_label

        def button(self, label: str, **_kwargs: Any) -> bool:
            return label == self.clicked_label

    monkeypatch.setattr(
        problems.st,
        "columns",
        lambda _count: [ActionColumn(""), ActionColumn("提交代码")],
    )
    monkeypatch.setattr(problems, "is_admin", lambda: False)
    monkeypatch.setattr(
        problems,
        "_open_view",
        lambda view, problem_id=None: opened.append((view, problem_id)),
    )

    problems.render_problem_actions("P1")

    assert opened == [("submit", "P1")]


class StubSidebar:
    def __init__(self) -> None:
        self.options: list[str] = []

    def radio(self, _label: str, options: list[str]) -> str:
        self.options = options
        return options[0]


def test_navigation_merges_problem_editor_and_profile_logout(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "info", lambda _message: None)
    monkeypatch.setattr(
        frontend_app,
        "get_current_user",
        lambda: {"username": "alice", "role": "user"},
    )
    monkeypatch.setattr(frontend_app, "is_admin", lambda: False)
    monkeypatch.setattr(frontend_app.profile, "render_page", lambda: None)

    frontend_app.build_navigation()

    assert sidebar.options == [
        "我的信息",
        "题目",
        "提交记录",
    ]
    assert "新增 / 编辑题目" not in sidebar.options
    assert "提交代码" not in sidebar.options
    assert "退出登录" not in sidebar.options


def test_navigation_keeps_user_management_admin_only(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "info", lambda _message: None)
    monkeypatch.setattr(
        frontend_app,
        "get_current_user",
        lambda: {"username": "admin", "role": "admin"},
    )
    monkeypatch.setattr(frontend_app, "is_admin", lambda: True)
    monkeypatch.setattr(frontend_app.profile, "render_page", lambda: None)

    frontend_app.build_navigation()

    assert "用户管理" in sidebar.options
    assert "新增 / 编辑题目" not in sidebar.options
    assert "提交代码" not in sidebar.options
    assert "退出登录" not in sidebar.options


def test_navigation_renders_login_form_for_guests(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    rendered: list[str] = []
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "info", lambda _message: None)
    monkeypatch.setattr(frontend_app, "get_current_user", lambda: None)
    monkeypatch.setattr(
        frontend_app.auth,
        "render_login_form",
        lambda: rendered.append("login"),
    )

    frontend_app.build_navigation()

    assert sidebar.options == ["登录", "注册"]
    assert rendered == ["login"]


def test_frontend_modules_import_from_streamlit_script_directory() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import api_client; "
                "import runpy; "
                "runpy.run_path('app.py', run_name='streamlit_startup_test')"
            ),
        ],
        cwd=PROJECT_ROOT / "frontend",
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, result.stderr
