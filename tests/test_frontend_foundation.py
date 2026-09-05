import subprocess
import sys
from pathlib import Path
from typing import Any

import requests

from frontend import api_client, ui
from frontend import app as frontend_app
from frontend import session as frontend_session
from frontend.pages import (
    auth,
    problem_editor,
    problems,
    profile,
    submission_detail,
    submissions,
    submit,
    users,
)

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
    state["problem_page_view"] = "submission_detail"
    state["submission_filters"] = {"user_id": "u1"}

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
    assert "problem_page_view" not in state
    assert "submission_filters" not in state
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
        cookies = requests.cookies.RequestsCookieJar()  # type: ignore

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


def test_submission_helpers_use_documented_api_contract(monkeypatch: Any) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    def fake_request_api(
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[int, dict[str, Any]]:
        calls.append((method, path, kwargs))
        return 200, {"code": 200, "msg": "success", "data": None}

    monkeypatch.setattr(api_client, "request_api", fake_request_api)

    api_client.list_languages()
    api_client.create_submission("P1", "python", "print(1)")
    api_client.list_submissions(
        user_id="u1",
        problem_id="P1",
        status="success",
        page=2,
        page_size=10,
    )
    api_client.get_submission("s1")
    api_client.get_submission_log("s1")
    api_client.rejudge_submission("s1")
    api_client.update_log_visibility("P1", True)
    api_client.list_log_access(
        user_id="u1",
        problem_id="P1",
        page=2,
        page_size=10,
    )

    assert calls == [
        ("GET", "/api/languages/", {}),
        (
            "POST",
            "/api/submissions/",
            {
                "json": {
                    "problem_id": "P1",
                    "language": "python",
                    "code": "print(1)",
                }
            },
        ),
        (
            "GET",
            "/api/submissions/",
            {
                "params": {
                    "user_id": "u1",
                    "problem_id": "P1",
                    "status": "success",
                    "page": 2,
                    "page_size": 10,
                }
            },
        ),
        ("GET", "/api/submissions/s1", {}),
        ("GET", "/api/submissions/s1/log", {}),
        ("PUT", "/api/submissions/s1/rejudge", {}),
        (
            "PUT",
            "/api/problems/P1/log_visibility",
            {"json": {"public_cases": True}},
        ),
        (
            "GET",
            "/api/logs/access/",
            {
                "params": {
                    "user_id": "u1",
                    "problem_id": "P1",
                    "page": 2,
                    "page_size": 10,
                }
            },
        ),
    ]


def test_login_response_requires_complete_user_identity() -> None:
    body = {
        "code": 200,
        "msg": "login success",
        "data": {"user_id": "u1", "username": "alice", "role": "user"},
    }

    assert auth._login_user_from_response(200, body) == body["data"]
    assert auth._login_user_from_response(401, body) is None
    assert (
        auth._login_user_from_response(
            200,
            {"code": 200, "msg": "login success", "data": {"username": "alice"}},
        )
        is None
    )


def test_show_api_message_reports_success_and_failures(monkeypatch: Any) -> None:
    successes: list[str] = []
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "success", successes.append)
    monkeypatch.setattr(ui.st, "error", errors.append)

    assert ui.show_api_message(
        200,
        {"code": 200, "msg": "success", "data": None},
        success_message="Saved.",
    )
    assert not ui.show_api_message(None, None)
    assert not ui.show_api_message(502, None)
    assert not ui.show_api_message(
        403,
        {"code": 403, "msg": "user is banned", "data": None},
    )

    assert successes == ["Saved."]
    assert errors == [
        "无法连接后端，请确认 FastAPI 服务已经启动。",
        "后端返回了非 JSON 响应（HTTP 502）。",
        "当前账号已被封禁。（HTTP 403，msg: user is banned）",
    ]


def test_show_api_message_can_validate_success_without_rendering(
    monkeypatch: Any,
) -> None:
    successes: list[str] = []
    monkeypatch.setattr(ui.st, "success", successes.append)

    assert ui.show_api_message(
        200,
        {"code": 200, "msg": "success", "data": []},
        show_success=False,
    )
    assert successes == []


def test_show_api_message_covers_required_status_codes(monkeypatch: Any) -> None:
    errors: list[str] = []
    monkeypatch.setattr(ui.st, "error", errors.append)

    expected_messages = {
        400: "请求参数无效，请检查提交的字段。（HTTP 400）",
        401: "需要登录或 Session 已过期，请重新登录。（HTTP 401）",
        403: "权限不足，或当前账号已被封禁。（HTTP 403）",
        404: "未找到请求的资源。（HTTP 404）",
        409: "资源状态冲突，请刷新后重试。（HTTP 409）",
        429: "请求过于频繁，请稍后重试。（HTTP 429）",
        500: "后端发生内部错误，请稍后重试。（HTTP 500）",
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
        "API 响应格式无效：HTTP 状态码 200 与 JSON code 400 不一致。",
        "API 响应格式无效：应包含 code（int）、msg（str）和 data 字段。",
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
    assert errors == ["此页面仅限 admin 访问。"]


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
    monkeypatch.setattr(
        profile, "render_profile", lambda _user: rendered.append("profile")
    )
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


def test_user_table_uses_single_row_selection(monkeypatch: Any) -> None:
    dataframe_kwargs: dict[str, Any] = {}
    listed_users = [
        {"user_id": "u1", "username": "alice", "role": "user"},
        {"user_id": "u2", "username": "bob", "role": "admin"},
    ]

    def fake_dataframe(_rows: Any, **kwargs: Any) -> dict[str, Any]:
        dataframe_kwargs.update(kwargs)
        return {"selection": {"rows": [1]}}

    monkeypatch.setattr(users.st, "dataframe", fake_dataframe)

    assert users.render_user_table(listed_users) == listed_users[1]
    assert dataframe_kwargs["selection_mode"] == "single-row"


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
    assert "title 为必填项。" in errors
    assert "samples 至少需要包含一项。" in errors
    assert "testcases[0] 必须包含字符串类型的 input 和 output。" in errors
    assert "time_limit 必须大于 0。" in errors
    assert "memory_limit 必须是大于 0 的整数。" in errors
    assert "tags 必须是字符串列表。" in errors


def test_new_problem_limits_are_editable_and_empty_by_default(
    monkeypatch: Any,
) -> None:
    number_inputs: list[tuple[str, dict[str, Any]]] = []
    text_inputs: list[tuple[str, str]] = []
    text_areas: list[str] = []
    submit_labels: list[str] = []

    class FormContext:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_args: Any) -> None:
            return None

    class ColumnContext(FormContext):
        pass

    monkeypatch.setattr(problem_editor.st, "session_state", {})
    monkeypatch.setattr(
        problem_editor, "get_current_user", lambda: {"username": "alice"}
    )
    monkeypatch.setattr(problem_editor.st, "form", lambda _key: FormContext())

    def fake_text_input(label: str, value: str = "", **_kwargs: Any) -> str:
        text_inputs.append((label, value))
        return value

    monkeypatch.setattr(
        problem_editor.st,
        "text_input",
        fake_text_input,
    )

    def fake_text_area(label: str, value: str = "", **_kwargs: Any) -> str:
        text_areas.append(label)
        return value

    monkeypatch.setattr(
        problem_editor.st,
        "text_area",
        fake_text_area,
    )
    monkeypatch.setattr(
        problem_editor.st,
        "columns",
        lambda *_args, **_kwargs: [ColumnContext(), ColumnContext()],
    )
    monkeypatch.setattr(
        problem_editor.st,
        "multiselect",
        lambda _label, options, default, **_kwargs: default,
    )
    monkeypatch.setattr(problem_editor.st, "markdown", lambda _message: None)
    monkeypatch.setattr(problem_editor.st, "caption", lambda _message: None)
    monkeypatch.setattr(
        problem_editor.st,
        "data_editor",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("samples 和 testcases 不应使用表格编辑")
        ),
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

    def fake_submit_button(label: str, **_kwargs: Any) -> bool:
        submit_labels.append(label)
        return False

    monkeypatch.setattr(
        problem_editor.st,
        "form_submit_button",
        fake_submit_button,
    )
    monkeypatch.setattr(
        problem_editor.st,
        "selectbox",
        lambda _label, options, index=0, **_kwargs: options[index],
    )

    assert problem_editor.render_problem_form() is None
    assert [label for label, _kwargs in number_inputs] == [
        "时间限制",
        "空间限制",
    ]
    assert all(kwargs["value"] is None for _label, kwargs in number_inputs)
    assert all("disabled" not in kwargs for _label, kwargs in number_inputs)
    assert ("作者", "alice") in text_inputs
    assert text_areas.count("输入") == 2
    assert text_areas.count("输出") == 2
    assert submit_labels[:2] == ["＋ 增加样例", "＋ 增加测试点"]


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


def test_problem_detail_actions_keep_edit_entry(monkeypatch: Any) -> None:
    opened: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        problems.st,
        "button",
        lambda label, **_kwargs: label == "编辑题目",
    )
    monkeypatch.setattr(problems, "is_admin", lambda: False)
    monkeypatch.setattr(
        problems,
        "_open_view",
        lambda view, problem_id=None: opened.append((view, problem_id)),
    )

    problems.render_problem_actions("P1")

    assert opened == [("edit", "P1")]


def test_problem_list_uses_single_row_table_selection(monkeypatch: Any) -> None:
    opened: list[tuple[str, str | None]] = []
    dataframe_kwargs: dict[str, Any] = {}

    def fake_dataframe(_rows: Any, **kwargs: Any) -> dict[str, Any]:
        dataframe_kwargs.update(kwargs)
        return {"selection": {"rows": [1]}}

    monkeypatch.setattr(problems.st, "dataframe", fake_dataframe)
    monkeypatch.setattr(problems.st, "caption", lambda _message: None)
    monkeypatch.setattr(
        problems.st,
        "selectbox",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("题目列表不应使用下拉框选择")
        ),
    )
    monkeypatch.setattr(problems.st, "button", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        problems,
        "_open_view",
        lambda view, problem_id=None: opened.append((view, problem_id)),
    )

    problems.render_problem_list(
        [{"id": "P1", "title": "甲"}, {"id": "P2", "title": "乙"}]
    )

    assert dataframe_kwargs["selection_mode"] == "single-row"
    assert dataframe_kwargs["on_select"] == "rerun"
    assert opened == [("detail", "P2")]


def test_problem_detail_renders_samples_and_testcases(monkeypatch: Any) -> None:
    rendered_fields: list[tuple[str, Any]] = []
    monkeypatch.setattr(problems, "render_problem_summary", lambda _problem: None)
    monkeypatch.setattr(problems.st, "markdown", lambda _message: None)
    monkeypatch.setattr(problems.st, "caption", lambda _message: None)

    class ExpanderContext:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_args: Any) -> None:
            return None

    expander_calls: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        problems.st,
        "expander",
        lambda label, expanded: (
            expander_calls.append((label, expanded)) or ExpanderContext()
        ),
    )
    monkeypatch.setattr(
        problems,
        "_render_io_cases",
        lambda field_name, cases: rendered_fields.append((field_name, cases)),
    )
    samples = [{"input": "1 2", "output": "3"}]
    testcases = [{"input": "2 3", "output": "5"}]

    problems.render_problem_detail(
        {
            "description": "加法",
            "input_description": "两个整数",
            "output_description": "和",
            "samples": samples,
            "constraints": "整数",
            "testcases": testcases,
        }
    )

    assert rendered_fields == [("samples", samples), ("testcases", testcases)]
    assert expander_calls == [("测试点", False)]


def test_problem_detail_places_submission_panel_on_right(monkeypatch: Any) -> None:
    rendered: list[str] = []
    problem = {"id": "P1", "title": "加法"}

    class ColumnContext:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_args: Any) -> None:
            return None

    monkeypatch.setattr(problems.st, "button", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        problems.st,
        "columns",
        lambda *args, **_kwargs: [ColumnContext(), ColumnContext()],
    )
    monkeypatch.setattr(problems.st, "divider", lambda: None)
    monkeypatch.setattr(problems, "load_problem_detail", lambda _problem_id: problem)
    monkeypatch.setattr(
        problems,
        "render_problem_detail",
        lambda _problem: rendered.append("题目详情"),
    )
    monkeypatch.setattr(
        problems,
        "render_problem_actions",
        lambda _problem_id: rendered.append("题目操作"),
    )
    monkeypatch.setattr(
        submit,
        "render_problem_submission",
        lambda _problem: rendered.append("代码提交"),
    )

    problems._render_detail_page("P1")

    assert rendered == ["题目详情", "题目操作", "代码提交"]


def test_submit_loaders_follow_problem_and_language_response_shapes(
    monkeypatch: Any,
) -> None:
    problem_options = [{"id": "P1", "title": "A+B"}]
    monkeypatch.setattr(
        submit,
        "list_problems",
        lambda: (200, {"code": 200, "msg": "success", "data": problem_options}),
    )
    monkeypatch.setattr(
        submit,
        "list_languages",
        lambda: (
            200,
            {"code": 200, "msg": "success", "data": {"name": ["python", "cpp"]}},
        ),
    )

    assert submit.load_problem_options() == problem_options
    assert submit.load_language_options() == ["python", "cpp"]


def test_submit_code_saves_valid_submission_id(monkeypatch: Any) -> None:
    selected: list[str] = []
    monkeypatch.setattr(
        submit,
        "create_submission",
        lambda *_args: (
            200,
            {
                "code": 200,
                "msg": "success",
                "data": {"submission_id": "s1", "status": "pending"},
            },
        ),
    )
    monkeypatch.setattr(submit, "show_api_message", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(submit, "set_selected_submission", selected.append)

    assert submit.submit_code("P1", "python", "print(1)") == "s1"
    assert selected == ["s1"]


def test_submission_list_loader_accepts_pending_items(monkeypatch: Any) -> None:
    rows = [
        {"submission_id": "s1", "status": "pending"},
        {"submission_id": "s2", "status": "success", "score": 10, "counts": 30},
    ]
    monkeypatch.setattr(
        submissions,
        "list_submissions",
        lambda **_kwargs: (
            200,
            {
                "code": 200,
                "msg": "success",
                "data": {"total": 2, "submissions": rows},
            },
        ),
    )

    assert submissions.load_submissions(user_id="u1", page=1, page_size=10) == (
        2,
        rows,
    )


def test_submission_detail_and_log_loaders_validate_shapes(monkeypatch: Any) -> None:
    detail = {
        "submission_id": "s1",
        "status": "success",
        "score": 20,
        "counts": 30,
        "compile_info": None,
        "run_info": {"result": "finished", "message": "done"},
        "error_info": "",
    }
    log = {
        "details": [{"id": 1, "result": "AC", "time": 0.1, "memory": 10}],
        "score": 20,
        "counts": 30,
    }
    monkeypatch.setattr(
        submission_detail,
        "get_submission",
        lambda _submission_id: (
            200,
            {"code": 200, "msg": "success", "data": detail},
        ),
    )
    monkeypatch.setattr(
        submission_detail,
        "get_submission_log",
        lambda _submission_id: (
            200,
            {"code": 200, "msg": "success", "data": log},
        ),
    )

    assert submission_detail.load_submission_detail("s1") == detail
    assert submission_detail.load_submission_log("s1") == log


def test_submission_log_403_is_reported_without_crashing(monkeypatch: Any) -> None:
    shown: list[tuple[int | None, Any]] = []
    body = {"code": 403, "msg": "permission denied", "data": None}
    monkeypatch.setattr(
        submission_detail,
        "get_submission_log",
        lambda _submission_id: (403, body),
    )
    monkeypatch.setattr(
        submission_detail,
        "show_api_message",
        lambda status_code, response, **_kwargs: shown.append((status_code, response)),
    )

    assert submission_detail.load_submission_log("s1") is None
    assert shown == [(403, body)]


def test_pending_submission_page_does_not_request_log(monkeypatch: Any) -> None:
    rendered: list[str] = []
    monkeypatch.setattr(submission_detail, "require_login", lambda: True)
    monkeypatch.setattr(submission_detail, "_render_back_button", lambda: None)
    monkeypatch.setattr(submission_detail, "get_selected_submission", lambda: "s1")
    monkeypatch.setattr(
        submission_detail,
        "load_submission_detail",
        lambda _submission_id: {"submission_id": "s1", "status": "pending"},
    )
    monkeypatch.setattr(
        submission_detail,
        "render_submission_detail",
        lambda _submission: rendered.append("detail"),
    )
    monkeypatch.setattr(
        submission_detail,
        "render_pending_state",
        lambda _submission_id: rendered.append("pending"),
    )
    monkeypatch.setattr(
        submission_detail,
        "load_submission_log",
        lambda _submission_id: (_ for _ in ()).throw(
            AssertionError("pending submissions must not request logs")
        ),
    )

    submission_detail.render_page()

    assert rendered == ["detail", "pending"]


def test_submission_status_renders_all_documented_states(monkeypatch: Any) -> None:
    rendered: list[tuple[str, str]] = []
    monkeypatch.setattr(
        ui.st, "info", lambda message: rendered.append(("info", message))
    )
    monkeypatch.setattr(
        ui.st,
        "success",
        lambda message: rendered.append(("success", message)),
    )
    monkeypatch.setattr(
        ui.st, "error", lambda message: rendered.append(("error", message))
    )

    ui.render_submission_status("pending")
    ui.render_submission_status("success")
    ui.render_submission_status("error")

    assert [kind for kind, _message in rendered] == ["info", "success", "error"]


class StubSidebar:
    def __init__(self) -> None:
        self.options: list[str] = []

    def button(self, label: str, **_kwargs: Any) -> bool:
        self.options.append(label)
        return False


def test_navigation_merges_problem_editor_and_profile_logout(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    monkeypatch.setattr(frontend_app.st, "session_state", {})
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "caption", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "info", lambda _message: None)
    monkeypatch.setattr(
        frontend_app,
        "get_current_user",
        lambda: {"username": "alice", "role": "user"},
    )
    monkeypatch.setattr(frontend_app, "is_admin", lambda: False)
    monkeypatch.setattr(frontend_app.problems, "render_page", lambda: None)

    frontend_app.build_navigation()

    assert sidebar.options == [
        "题目",
        "评测结果",
    ]
    assert "新增/修改题目" not in sidebar.options
    assert "提交代码" not in sidebar.options
    assert "退出登录" not in sidebar.options


def test_navigation_keeps_user_management_admin_only(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    monkeypatch.setattr(frontend_app.st, "session_state", {})
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "caption", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "info", lambda _message: None)
    monkeypatch.setattr(
        frontend_app,
        "get_current_user",
        lambda: {"username": "admin", "role": "admin"},
    )
    monkeypatch.setattr(frontend_app, "is_admin", lambda: True)
    monkeypatch.setattr(frontend_app.problems, "render_page", lambda: None)

    frontend_app.build_navigation()

    assert "用户管理" in sidebar.options
    assert "新增/修改题目" not in sidebar.options
    assert "提交代码" not in sidebar.options
    assert "退出登录" not in sidebar.options


def test_navigation_renders_login_form_for_guests(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    rendered: list[str] = []
    monkeypatch.setattr(frontend_app.st, "session_state", {})
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "caption", lambda _message: None)
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


def test_navigation_opens_submission_records(monkeypatch: Any) -> None:
    sidebar = StubSidebar()
    rendered: list[str] = []
    monkeypatch.setattr(
        frontend_app.st,
        "session_state",
        {"navigation_page": "评测结果"},
    )
    monkeypatch.setattr(frontend_app.st, "sidebar", sidebar)
    monkeypatch.setattr(frontend_app.st, "header", lambda _message: None)
    monkeypatch.setattr(frontend_app.st, "caption", lambda _message: None)
    monkeypatch.setattr(
        frontend_app,
        "get_current_user",
        lambda: {"username": "alice", "role": "user"},
    )
    monkeypatch.setattr(frontend_app, "is_admin", lambda: False)
    monkeypatch.setattr(
        frontend_app.submissions,
        "render_page",
        lambda: rendered.append("submissions"),
    )

    frontend_app.build_navigation()

    assert rendered == ["submissions"]


def test_submission_selector_offers_result_and_log_actions(monkeypatch: Any) -> None:
    labels: list[str] = []

    class ActionColumn:
        def button(self, label: str, **_kwargs: Any) -> bool:
            labels.append(label)
            return False

    monkeypatch.setattr(submissions.st, "caption", lambda _message: None)
    monkeypatch.setattr(
        submissions.st,
        "columns",
        lambda _count: [ActionColumn(), ActionColumn()],
    )

    submissions.render_submission_selector("s1")

    assert labels == ["查询选中评测结果", "查询选中评测日志"]


def test_submission_table_uses_single_row_selection(monkeypatch: Any) -> None:
    dataframe_kwargs: dict[str, Any] = {}
    rendered_rows: list[dict[str, Any]] = []

    def fake_dataframe(rows: Any, **kwargs: Any) -> dict[str, Any]:
        rendered_rows.extend(rows)
        dataframe_kwargs.update(kwargs)
        return {"selection": {"rows": [0]}}

    monkeypatch.setattr(submissions.st, "dataframe", fake_dataframe)

    selected = submissions.render_submission_table(
        [
            {
                "submission_id": "s1",
                "status": "success",
                "score": 100,
                "counts": 10,
            },
            {
                "submission_id": "s2",
                "status": "pending",
                "score": None,
                "counts": None,
            },
        ]
    )

    assert selected == "s1"
    assert dataframe_kwargs["selection_mode"] == "single-row"
    assert [row["得分"] for row in rendered_rows] == [100, None]
    assert [row["测试点数"] for row in rendered_rows] == [10, None]


def test_streamlit_builtin_page_navigation_is_disabled() -> None:
    config = (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")

    assert "showSidebarNavigation = false" in config


def test_readme_limits_uvicorn_reload_to_backend_source() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "uvicorn app.main:app --reload --reload-dir app" in readme


def test_frontend_uses_chinese_navigation_and_preserves_api_fields() -> None:
    app_source = (PROJECT_ROOT / "frontend" / "app.py").read_text(encoding="utf-8")
    submissions_source = (
        PROJECT_ROOT / "frontend" / "pages" / "submissions.py"
    ).read_text(encoding="utf-8")

    assert all(label in app_source for label in ("题目", "评测结果", "我的信息"))
    assert all(
        field in submissions_source
        for field in ("user_id", "problem_id", "status", "page", "page_size")
    )


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
