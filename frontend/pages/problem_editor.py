from typing import Any

import streamlit as st

if __package__ == "frontend.pages":
    from ..api_client import create_problem, get_problem, update_problem
    from ..session import get_selected_problem, set_selected_problem
    from ..ui import require_login, show_api_message
else:
    from api_client import create_problem, get_problem, update_problem
    from session import get_selected_problem, set_selected_problem
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
    """编辑 samples。"""
    rows = _normalize_io_rows(initial_samples) or [{"input": "", "output": ""}]
    edited = st.data_editor(
        rows,
        key=_editor_key("samples"),
        num_rows="dynamic",
        use_container_width=True,
        column_order=["input", "output"],
    )
    return _normalize_io_rows(edited)


def render_testcases_editor(
    initial_testcases: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """编辑 testcases。"""
    rows = _normalize_io_rows(initial_testcases) or [{"input": "", "output": ""}]
    edited = st.data_editor(
        rows,
        key=_editor_key("testcases"),
        num_rows="dynamic",
        use_container_width=True,
        column_order=["input", "output"],
    )
    return _normalize_io_rows(edited)


def render_problem_form(
    initial_data: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    渲染题目表单。
    用户提交时返回 problem_data，否则返回 None。
    """
    initial = initial_data or {}
    editing = initial_data is not None
    tags = initial.get("tags", [])
    initial_tags = [str(tag) for tag in tags] if isinstance(tags, list) else []
    initial_time_limit = initial.get("time_limit")
    initial_memory_limit = initial.get("memory_limit")

    with st.form(_editor_key("form")):
        problem_id = st.text_input(
            "id",
            value=str(initial.get("id", "")),
            disabled=editing,
            help="必填",
        )
        title = st.text_input(
            "title",
            value=str(initial.get("title", "")),
            help="必填",
        )
        description = st.text_area(
            "description",
            value=str(initial.get("description", "")),
            height=160,
            help="必填",
        )
        input_description = st.text_area(
            "input_description",
            value=str(initial.get("input_description", "")),
            help="必填",
        )
        output_description = st.text_area(
            "output_description",
            value=str(initial.get("output_description", "")),
            help="必填",
        )
        constraints = st.text_area(
            "constraints",
            value=str(initial.get("constraints", "")),
            help="必填",
        )

        st.markdown("#### samples")
        samples = render_samples_editor(initial.get("samples"))
        st.caption("可用表格末尾的空行添加样例，也可选中行后删除。")

        st.markdown("#### testcases")
        testcases = render_testcases_editor(initial.get("testcases"))
        st.caption("所有测试点都会保存到题目配置，并用于评测提交。")

        hint = st.text_area("hint", value=str(initial.get("hint", "")))
        source = st.text_input("source", value=str(initial.get("source", "")))
        selected_tags = st.multiselect(
            "tags",
            options=initial_tags,
            default=initial_tags,
            accept_new_options=True,
            help="可选择已有 tags，也可输入新的 tag。",
        )
        author = st.text_input("author", value=str(initial.get("author", "")))
        difficulty_options = ["", "easy", "medium", "hard"]
        initial_difficulty = str(initial.get("difficulty", ""))
        if initial_difficulty and initial_difficulty not in difficulty_options:
            difficulty_options.append(initial_difficulty)
        difficulty = st.selectbox(
            "difficulty",
            difficulty_options,
            index=difficulty_options.index(initial_difficulty),
        )

        time_limit_value = st.number_input(
            "time_limit",
            min_value=0.01,
            value=(
                float(initial_time_limit)
                if initial_time_limit is not None
                else None
            ),
            step=0.1,
            placeholder="留空时使用语言配置或系统默认值",
            help="单位: 秒",
        )
        memory_limit_value = st.number_input(
            "memory_limit",
            min_value=1,
            value=(
                int(initial_memory_limit)
                if initial_memory_limit is not None
                else None
            ),
            step=1,
            placeholder="留空时使用语言配置或系统默认值",
            help="单位: MB",
        )

        submitted = st.form_submit_button(
            "保存修改" if editing else "创建题目",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
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
    前端基础格式检查。
    返回错误信息列表。
    后端仍必须再次完整校验。
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
            errors.append(f"{label}不能为空。")

    for field, label in (("samples", "样例"), ("testcases", "测试点")):
        rows = problem_data.get(field)
        if not isinstance(rows, list) or not rows:
            errors.append(f"至少需要填写一组{label}。")
            continue
        for index, row in enumerate(rows, start=1):
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("input"), str)
                or not isinstance(row.get("output"), str)
            ):
                errors.append(f"第 {index} 组{label}必须包含字符串 input 和 output。")

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
    """调用新增题目接口。"""
    errors = validate_problem_form(problem_data)
    if errors:
        _show_validation_errors(errors)
        return

    status_code, body = create_problem(problem_data)
    if not show_api_message(status_code, body):
        return

    set_selected_problem(problem_data["id"])
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_NOTICE_KEY] = f"题目 {problem_data['id']} 创建成功。"
    st.rerun()


def update_problem_from_form(
    problem_id: str,
    problem_data: dict[str, Any],
) -> None:
    """调用编辑题目接口。"""
    errors = validate_problem_form(problem_data)
    if problem_data.get("id") != problem_id:
        errors.append("请求体中的 id 必须与 URL 中的 problem_id 一致。")
    if errors:
        _show_validation_errors(errors)
        return

    status_code, body = update_problem(problem_id, problem_data)
    if not show_api_message(status_code, body):
        return

    set_selected_problem(problem_id)
    st.session_state[_VIEW_KEY] = "detail"
    st.session_state[_NOTICE_KEY] = f"题目 {problem_id} 更新成功。"
    st.rerun()


def _load_problem_for_edit(problem_id: str) -> dict[str, Any] | None:
    status_code, body = get_problem(problem_id)
    if status_code != 200 or body is None or body.get("code") != 200:
        show_api_message(status_code, body)
        return None
    problem = body.get("data")
    if not isinstance(problem, dict):
        st.error("后端题目详情响应格式异常。")
        return None
    return problem


def render_page() -> None:
    """题目新增 / 编辑页面入口。"""
    if not require_login():
        return

    mode = str(st.session_state.get(_VIEW_KEY, "create"))
    if mode == "edit":
        problem_id = get_selected_problem()
        if not problem_id:
            st.error("没有选择要编辑的题目。")
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
    st.subheader("新增题目")
    problem_data = render_problem_form()
    if problem_data is not None:
        create_problem_from_form(problem_data)
