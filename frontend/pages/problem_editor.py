from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import create_problem, get_problem, update_problem
    from ..session import get_current_user, get_selected_problem, set_selected_problem
    from ..ui import require_login, show_api_message
else:
    from api_client import create_problem, get_problem, update_problem
    from session import get_current_user, get_selected_problem, set_selected_problem
    from ui import require_login, show_api_message


_VIEW_KEY = "problem_page_view"
_NOTICE_KEY = "problem_notice"
_EDITOR_CONTEXT_KEY = "problem_editor_context"


def _editor_key(name: str) -> str:
    context = str(st.session_state.get(_EDITOR_CONTEXT_KEY, "new"))
    return f"problem_editor_{context}_{name}"


def _normalize_io_rows(value: Any) -> list[dict[str, str]]:
    if hasattr(value, "to_dict"):
        value = value.to_dict("records")
    if not isinstance(value, list):
        return []

    rows: list[dict[str, str]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        input_value = row.get("input", "")
        output_value = row.get("output", "")
        rows.append(
            {
                "input": "" if input_value is None else str(input_value),
                "output": "" if output_value is None else str(output_value),
            }
        )
    return rows


def render_samples_editor(
    initial_samples: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """使用左右并排的文本框编辑 samples。"""
    return _render_io_editors("samples", initial_samples)


def render_testcases_editor(
    initial_testcases: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """使用左右并排的文本框编辑 testcases。"""
    return _render_io_editors("testcases", initial_testcases)


def _render_io_editors(
    field_name: str,
    initial_rows: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    normalized = _normalize_io_rows(initial_rows) or [{"input": "", "output": ""}]
    count_key = _editor_key(f"{field_name}_count")
    if count_key not in st.session_state:
        st.session_state[count_key] = len(normalized)
    row_count = max(1, int(st.session_state[count_key]))

    rows: list[dict[str, str]] = []
    for index in range(row_count):
        initial = normalized[index] if index < len(normalized) else {}
        item_name = "样例" if field_name == "samples" else "测试点"
        st.caption(f"{item_name} {index + 1}")
        input_column, output_column = st.columns(2, gap="medium")
        with input_column:
            input_value = st.text_area(
                "输入",
                value=str(initial.get("input", "")),
                key=_editor_key(f"{field_name}_{index}_input"),
                height=112,
            )
        with output_column:
            output_value = st.text_area(
                "输出",
                value=str(initial.get("output", "")),
                key=_editor_key(f"{field_name}_{index}_output"),
                height=112,
            )
        rows.append({"input": input_value, "output": output_value})
    return rows


def render_problem_form(
    initial_data: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Render the problem form and return problem_data after submission.
    """
    initial = initial_data or {}
    editing = initial_data is not None
    tags = initial.get("tags", [])
    initial_tags = [str(tag) for tag in tags] if isinstance(tags, list) else []
    initial_time_limit = initial.get("time_limit")
    initial_memory_limit = initial.get("memory_limit")
    current_user = get_current_user() or {}
    default_author = str(current_user.get("username", "")) if not editing else ""

    with st.form(_editor_key("form")):
        problem_id = st.text_input(
            "题目编号",
            value=str(initial.get("id", "")),
            disabled=editing,
            help="必填",
        )
        title = st.text_input(
            "题目名称",
            value=str(initial.get("title", "")),
            help="必填",
        )
        description = st.text_area(
            "题目描述",
            value=str(initial.get("description", "")),
            height=160,
            help="必填",
        )
        input_description = st.text_area(
            "输入说明",
            value=str(initial.get("input_description", "")),
            help="必填",
        )
        output_description = st.text_area(
            "输出说明",
            value=str(initial.get("output_description", "")),
            help="必填",
        )
        constraints = st.text_area(
            "数据范围",
            value=str(initial.get("constraints", "")),
            help="必填",
        )

        st.markdown("#### 样例")
        samples = render_samples_editor(initial.get("samples"))
        add_sample = st.form_submit_button("＋ 增加样例")

        st.markdown("#### 测试点")
        testcases = render_testcases_editor(initial.get("testcases"))
        add_testcase = st.form_submit_button("＋ 增加测试点")

        hint = st.text_area("提示", value=str(initial.get("hint", "")))
        source = st.text_input("来源", value=str(initial.get("source", "")))
        selected_tags = st.multiselect(
            "标签",
            options=initial_tags,
            default=initial_tags,
            accept_new_options=True,
            help="选择已有标签，或直接输入新标签。",
        )
        author = st.text_input(
            "作者",
            value=str(initial.get("author", default_author)),
        )
        difficulty_options = ["", "easy", "medium", "hard"]
        initial_difficulty = str(initial.get("difficulty", ""))
        if initial_difficulty and initial_difficulty not in difficulty_options:
            difficulty_options.append(initial_difficulty)
        difficulty = st.selectbox(
            "难度",
            difficulty_options,
            index=difficulty_options.index(initial_difficulty),
            format_func=lambda value: {
                "": "未设置",
                "easy": "简单",
                "medium": "中等",
                "hard": "困难",
            }.get(value, value),  # type: ignore
        )  # type: ignore

        time_limit_value = st.number_input(
            "时间限制",
            min_value=0.01,
            value=(
                float(initial_time_limit) if initial_time_limit is not None else None
            ),
            step=0.1,
            placeholder="留空时使用 language 或系统默认值",
            help="单位：秒；作业 API 允许置空",
        )
        memory_limit_value = st.number_input(
            "空间限制",
            min_value=1,
            value=(
                int(initial_memory_limit) if initial_memory_limit is not None else None
            ),
            step=1,
            placeholder="留空时使用 language 或系统默认值",
            help="单位：MB；作业 API 允许置空",
        )

        submitted = st.form_submit_button(
            "保存修改" if editing else "创建题目",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        if add_sample:
            sample_count_key = _editor_key("samples_count")
            st.session_state[sample_count_key] = (
                int(st.session_state.get(sample_count_key, 1)) + 1
            )
            st.rerun()
        if add_testcase:
            testcase_count_key = _editor_key("testcases_count")
            st.session_state[testcase_count_key] = (
                int(st.session_state.get(testcase_count_key, 1)) + 1
            )
            st.rerun()
        return None

    return {
        "id": problem_id.strip(),
        "title": title.strip(),
        "description": description.strip(),
        "input_description": input_description.strip(),
        "output_description": output_description.strip(),
        "samples": samples,
        "constraints": constraints.strip(),
        "testcases": testcases,
        "hint": hint.strip(),
        "source": source.strip(),
        "tags": [str(tag).strip() for tag in selected_tags if str(tag).strip()],
        "time_limit": (
            float(time_limit_value) if time_limit_value is not None else None
        ),
        "memory_limit": (
            int(memory_limit_value) if memory_limit_value is not None else None
        ),
        "author": author.strip(),
        "difficulty": difficulty.strip(),
    }


def validate_problem_form(problem_data: dict[str, Any]) -> list[str]:
    """
    Perform basic client-side validation. The backend remains authoritative.
    """
    errors: list[str] = []
    required_text = {
        "id": "id",
        "title": "title",
        "description": "description",
        "input_description": "input_description",
        "output_description": "output_description",
        "constraints": "constraints",
    }
    for field, label in required_text.items():
        value = problem_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label} 为必填项。")

    for field in ("samples", "testcases"):
        rows = problem_data.get(field)
        if not isinstance(rows, list) or not rows:
            errors.append(f"{field} 至少需要包含一项。")
            continue
        for index, row in enumerate(rows, start=1):
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("input"), str)
                or not isinstance(row.get("output"), str)
            ):
                errors.append(
                    f"{field}[{index - 1}] 必须包含字符串类型的 input 和 output。"
                )

    time_limit = problem_data.get("time_limit")
    if time_limit is not None and (
        not isinstance(time_limit, (int, float)) or time_limit <= 0
    ):
        errors.append("time_limit 必须大于 0。")
    memory_limit = problem_data.get("memory_limit")
    if memory_limit is not None and (
        not isinstance(memory_limit, int)
        or isinstance(memory_limit, bool)
        or memory_limit <= 0
    ):
        errors.append("memory_limit 必须是大于 0 的整数。")

    tags = problem_data.get("tags")
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        errors.append("tags 必须是字符串列表。")
    return errors


def _show_validation_errors(errors: list[str]) -> None:
    for error in errors:
        st.error(error)


def create_problem_from_form(problem_data: dict[str, Any]) -> None:
    """Create a problem through POST /api/problems/."""
    errors = validate_problem_form(problem_data)
    if errors:
        _show_validation_errors(errors)
        return

    status_code, body = create_problem(problem_data)
    if not show_api_message(status_code, body):
        return

    set_selected_problem(problem_data["id"])
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_NOTICE_KEY] = f"题目 {problem_data['id']} 已创建。"
    st.rerun()


def update_problem_from_form(
    problem_id: str,
    problem_data: dict[str, Any],
) -> None:
    """Update a problem through PUT /api/problems/{problem_id}."""
    errors = validate_problem_form(problem_data)
    if problem_data.get("id") != problem_id:
        errors.append("请求体字段 id 必须与 URL 参数 problem_id 一致。")
    if errors:
        _show_validation_errors(errors)
        return

    status_code, body = update_problem(problem_id, problem_data)
    if not show_api_message(status_code, body):
        return

    set_selected_problem(problem_id)
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_NOTICE_KEY] = f"题目 {problem_id} 已更新。"
    st.rerun()


def _load_problem_for_edit(problem_id: str) -> dict[str, Any] | None:
    status_code, body = get_problem(problem_id)
    if not show_api_message(status_code, body, show_success=False):
        return None
    problem = body.get("data")  # type: ignore
    if not isinstance(problem, dict):
        st.error("API 响应格式无效：data 应包含题目对象。")
        return None
    return problem


def render_page() -> None:
    """Render the create or edit problem page."""
    if not require_login():
        return

    mode = str(st.session_state.get(_VIEW_KEY, "create"))
    if mode == "edit":
        problem_id = get_selected_problem()
        if not problem_id:
            st.error("请先选择需要编辑的题目。")
            st.session_state[_VIEW_KEY] = "list"
            return
        st.session_state[_EDITOR_CONTEXT_KEY] = f"edit_{problem_id}"
        st.subheader(f"编辑题目 · {problem_id}")
        initial_data = _load_problem_for_edit(problem_id)
        if initial_data is None:
            return
        problem_data = render_problem_form(initial_data)
        if problem_data is not None:
            update_problem_from_form(problem_id, problem_data)
        return

    st.session_state[_EDITOR_CONTEXT_KEY] = "create"
    st.subheader("创建题目")
    problem_data = render_problem_form()
    if problem_data is not None:
        create_problem_from_form(problem_data)
