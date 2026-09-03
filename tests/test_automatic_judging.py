import asyncio
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import DATABASE_PATH
from app.judge import evaluator, runner
from app.judge.comparator import compare_output
from app.judge.evaluator import evaluate_language
from app.main import app
from app.models.enums import JudgeResult
from app.models.judge import ProcessRunResult
from app.models.language import LanguagePublic
from app.models.problem import TestCase as JudgeTestCase
from app.services import language_service


def make_testcase(input_data: str, output: str) -> JudgeTestCase:
    return JudgeTestCase(input=input_data, output=output)


def make_python_language(
    time_limit: float,
    memory_limit: int,
) -> LanguagePublic:
    return LanguagePublic(
        name="python",
        file_ext=".py",
        compile_cmd=None,
        run_cmd=runner.PYTHON_RUN_COMMAND,
        time_limit=time_limit,
        memory_limit=memory_limit,
    )


def make_cpp_language(
    time_limit: float,
    memory_limit: int,
) -> LanguagePublic:
    return LanguagePublic(
        name="cpp",
        file_ext=".cpp",
        compile_cmd="g++ {src} -std=c++14 -o {exe}",
        run_cmd="{exe}",
        time_limit=time_limit,
        memory_limit=memory_limit,
    )


async def evaluate_python(
    source_code: str,
    testcases: list[JudgeTestCase],
    time_limit: float,
    memory_limit: int = 128,
):
    return await evaluate_language(
        source_code,
        testcases,
        time_limit,
        memory_limit,
        make_python_language(time_limit, memory_limit),
    )


async def evaluate_cpp(
    source_code: str,
    testcases: list[JudgeTestCase],
    time_limit: float,
    memory_limit: int = 128,
):
    return await evaluate_language(
        source_code,
        testcases,
        time_limit,
        memory_limit,
        make_cpp_language(time_limit, memory_limit),
    )


def test_language_list_and_registration() -> None:
    language_name = f"language_{uuid4().hex[:8]}"
    compiled_language_name = f"language_cpp_{uuid4().hex[:8]}"
    username = f"testlanguage_{uuid4().hex[:8]}"
    try:
        with TestClient(app) as client:
            list_response = client.get("/api/languages/")
            unauthorized = client.post("/api/languages/", json={})
            client.post(
                "/api/users/",
                json={"username": username, "password": "secret1"},
            )
            client.post(
                "/api/auth/login",
                json={"username": username, "password": "secret1"},
            )
            create_response = client.post(
                "/api/languages/",
                json={
                    "name": language_name,
                    "file_ext": ".txt",
                    "compile_cmd": None,
                    "run_cmd": runner.PYTHON_RUN_COMMAND,
                },
            )
            compiled_response = client.post(
                "/api/languages/",
                json={
                    "name": compiled_language_name,
                    "file_ext": ".cpp",
                    "compile_cmd": "g++ {src} -std=c++14 -o {exe}",
                    "run_cmd": "{exe}",
                },
            )
            updated_list = client.get("/api/languages/")

        interpreted_language = asyncio.run(
            language_service.get_language(language_name)
        )
        compiled_language = asyncio.run(
            language_service.get_language(compiled_language_name)
        )
        interpreted_result = asyncio.run(
            evaluate_language(
                "print(int(input()) * 2)",
                [make_testcase("3\n", "6\n")],
                1.0,
                128,
                interpreted_language,
            )
        )
        compiled_result = asyncio.run(
            evaluate_language(
                """
#include <iostream>
int main() {
    int value;
    std::cin >> value;
    std::cout << value * 2 << std::endl;
    return 0;
}
""",
                [make_testcase("3\n", "6\n")],
                2.0,
                128,
                compiled_language,
            )
        )

        assert list_response.status_code == status.HTTP_200_OK
        assert {"python", "cpp"}.issubset(list_response.json()["data"]["name"])
        assert unauthorized.status_code == status.HTTP_401_UNAUTHORIZED
        assert create_response.status_code == status.HTTP_200_OK
        assert create_response.json() == {
            "code": status.HTTP_200_OK,
            "msg": "language registered",
            "data": {"name": language_name},
        }
        assert compiled_response.status_code == status.HTTP_200_OK
        assert language_name in updated_list.json()["data"]["name"]
        assert compiled_language_name in updated_list.json()["data"]["name"]
        assert interpreted_result.result == JudgeResult.AC
        assert compiled_result.result == JudgeResult.AC
    finally:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute(
                "DELETE FROM languages WHERE name IN (?, ?)",
                (language_name, compiled_language_name),
            )
            db.execute("DELETE FROM users WHERE username = ?", (username,))
            db.commit()


def test_language_registration_allows_new_toolchains_and_checks_templates() -> None:
    username = f"testlanguage_{uuid4().hex[:8]}"
    language_names = [f"language_open_{uuid4().hex[:8]}" for _ in range(3)]
    new_toolchains = [
        {"compile_cmd": None, "run_cmd": "node {src}"},
        {
            "compile_cmd": "javac {src}",
            "run_cmd": "java Main",
        },
        {
            "compile_cmd": "go build -o {exe} {src}",
            "run_cmd": "{exe}",
        },
    ]
    try:
        with TestClient(app) as client:
            client.post(
                "/api/users/",
                json={"username": username, "password": "secret1"},
            )
            client.post(
                "/api/auth/login",
                json={"username": username, "password": "secret1"},
            )
            accepted_responses = [
                client.post(
                    "/api/languages/",
                    json={
                        "name": language_name,
                        "file_ext": ".txt",
                        **commands,
                    },
                )
                for language_name, commands in zip(language_names, new_toolchains)
            ]
            invalid_placeholder = client.post(
                "/api/languages/",
                json={
                    "name": f"language_invalid_{uuid4().hex[:8]}",
                    "file_ext": ".txt",
                    "compile_cmd": None,
                    "run_cmd": "python {source}",
                },
            )

        assert all(
            response.status_code == status.HTTP_200_OK
            for response in accepted_responses
        )
        assert invalid_placeholder.status_code == status.HTTP_400_BAD_REQUEST
    finally:
        with sqlite3.connect(DATABASE_PATH) as db:
            db.executemany(
                "DELETE FROM languages WHERE name = ?",
                [(language_name,) for language_name in language_names],
            )
            db.execute("DELETE FROM users WHERE username = ?", (username,))
            db.commit()


@pytest.mark.asyncio
async def test_dynamic_language_runs_from_temp_path_with_spaces(
    tmp_path: Path,
    monkeypatch,
) -> None:
    temp_dir = tmp_path / "judge temporary files"
    temp_dir.mkdir()
    monkeypatch.setattr(runner, "TEMP_DIR", temp_dir)
    result = await evaluate_language(
        "print(int(input()) * 2)",
        [make_testcase("3\n", "6\n")],
        1.0,
        128,
        LanguagePublic(
            name="python_alias",
            file_ext=".py",
            compile_cmd=None,
            run_cmd=runner.PYTHON_RUN_COMMAND,
        ),
    )

    assert result.result == JudgeResult.AC
    assert list(temp_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_accepted_result() -> None:
    result = await evaluate_python(
        "a, b = map(int, input().split())\nprint(a + b)",
        [make_testcase("1 2\n", "3\n")],
        1.0,
    )
    assert result.result == JudgeResult.AC
    assert result.score == 10
    assert result.counts == 10


@pytest.mark.asyncio
async def test_wrong_answer_result() -> None:
    result = await evaluate_python(
        "print(0)",
        [make_testcase("", "3\n")],
        1.0,
    )
    assert result.result == JudgeResult.WA
    assert result.score == 0


@pytest.mark.asyncio
async def test_runtime_error_result() -> None:
    result = await evaluate_python(
        "print(1 / 0)",
        [make_testcase("", "0\n")],
        1.0,
    )
    assert result.result == JudgeResult.RE


@pytest.mark.asyncio
async def test_time_limit_exceeded_result() -> None:
    result = await evaluate_python(
        "while True:\n    pass",
        [make_testcase("", "")],
        0.05,
    )
    assert result.result == JudgeResult.TLE


@pytest.mark.asyncio
async def test_multiple_testcases_use_ten_points_each() -> None:
    result = await evaluate_python(
        "print(int(input()) * 2)",
        [
            make_testcase("2\n", "4\n"),
            make_testcase("3\n", "6\n"),
            make_testcase("4\n", "9\n"),
        ],
        1.0,
    )
    assert result.result == JudgeResult.WA
    assert result.score == 20
    assert result.counts == 30
    assert [case.result for case in result.cases] == [
        JudgeResult.AC,
        JudgeResult.AC,
        JudgeResult.WA,
    ]


@pytest.mark.asyncio
async def test_invalid_utf8_is_runtime_error() -> None:
    result = await evaluate_python(
        "import sys\nsys.stdout.buffer.write(b'\\xff')",
        [make_testcase("", "")],
        1.0,
    )
    assert result.result == JudgeResult.RE


@pytest.mark.asyncio
async def test_system_error_is_unknown(monkeypatch) -> None:
    async def fail_run(*args, **kwargs) -> ProcessRunResult:
        return ProcessRunResult(system_error="OSError")

    monkeypatch.setattr(evaluator, "run_language_case", fail_run)
    result = await evaluate_python(
        "print(1)",
        [make_testcase("", "1\n")],
        1.0,
    )
    assert result.result == JudgeResult.UNK


@pytest.mark.asyncio
async def test_temporary_files_are_removed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "TEMP_DIR", tmp_path)
    result = await runner.run_language_case(
        "print(1)",
        "",
        1.0,
        128,
        make_python_language(1.0, 128),
    )
    assert result.exit_code == 0
    assert list(tmp_path.iterdir()) == []


def test_compare_output_ignores_trailing_spaces() -> None:
    assert compare_output("3   \n", "3\n") is True


def test_compare_output_ignores_trailing_tabs() -> None:
    assert compare_output("3\t\t\n", "3\n") is True


def test_compare_output_normalizes_windows_newlines() -> None:
    assert compare_output("1\r\n2\r\n", "1\n2\n") is True


def test_compare_output_normalizes_carriage_returns() -> None:
    assert compare_output("1\r2\r", "1\n2\n") is True


def test_compare_output_ignores_extra_final_blank_lines() -> None:
    assert compare_output("3\n\n\n", "3\n") is True


def test_compare_output_preserves_leading_spaces() -> None:
    assert compare_output("  3\n", "3\n") is False


def test_compare_output_preserves_internal_spaces() -> None:
    assert compare_output("1  2\n", "1 2\n") is False


def test_compare_output_rejects_extra_prompt_text() -> None:
    assert compare_output("答案是 3", "3") is False


@pytest.mark.asyncio
async def test_cpp_compilation_execution_and_compile_error() -> None:
    accepted = await evaluate_cpp(
        """
#include <iostream>
int main() {
    int a, b;
    std::cin >> a >> b;
    std::cout << a + b << std::endl;
    return 0;
}
""",
        [make_testcase("1 2\n", "3\n")],
        2.0,
        128,
    )
    compile_error = await evaluate_cpp(
        "int main( {",
        [make_testcase("", "")],
        2.0,
        128,
    )
    assert accepted.result == JudgeResult.AC
    assert compile_error.result == JudgeResult.CE
    assert compile_error.compile_info
    assert str(runner.TEMP_DIR) not in compile_error.compile_info


@pytest.mark.parametrize(
    ("compile_result", "expected_message"),
    [
        (ProcessRunResult(timed_out=True), "compilation timed out"),
        (
            ProcessRunResult(memory_exceeded=True),
            "compilation memory limit exceeded",
        ),
    ],
)
@pytest.mark.asyncio
async def test_compile_limit_exceeded_is_compilation_error(
    monkeypatch,
    compile_result: ProcessRunResult,
    expected_message: str,
) -> None:
    async def return_compile_result(*args, **kwargs) -> ProcessRunResult:
        return compile_result

    monkeypatch.setattr(runner, "execute_process", return_compile_result)
    result = await evaluate_cpp(
        "int main() { return 0; }",
        [make_testcase("", "")],
        1.0,
        128,
    )

    assert result.result == JudgeResult.CE
    assert result.compile_info == expected_message


@pytest.mark.parametrize(
    ("run_result", "expected_result"),
    [
        (ProcessRunResult(timed_out=True), JudgeResult.TLE),
        (ProcessRunResult(memory_exceeded=True), JudgeResult.MLE),
    ],
)
@pytest.mark.asyncio
async def test_run_limit_exceeded_keeps_runtime_result(
    monkeypatch,
    run_result: ProcessRunResult,
    expected_result: JudgeResult,
) -> None:
    process_results = [ProcessRunResult(exit_code=0), run_result]

    async def return_next_result(*args, **kwargs) -> ProcessRunResult:
        return process_results.pop(0)

    monkeypatch.setattr(runner, "execute_process", return_next_result)
    result = await evaluate_cpp(
        "int main() { return 0; }",
        [make_testcase("", "")],
        1.0,
        128,
    )

    assert result.result == expected_result
    assert result.compile_info is None


@pytest.mark.asyncio
async def test_memory_limit_exceeded_result() -> None:
    result = await evaluate_python(
        (
            "import time\n"
            "data = bytearray(128 * 1024 * 1024)\n"
            "time.sleep(0.2)\n"
            "print(len(data))"
        ),
        [make_testcase("", "134217728\n")],
        2.0,
        32,
    )
    assert result.result == JudgeResult.MLE
