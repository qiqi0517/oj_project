import asyncio
import os
import shlex
import shutil
import sys
import time
from pathlib import Path
from uuid import uuid4

import psutil

from app.config import TEMP_DIR
from app.models.judge import ProcessRunResult
from app.models.language import LanguagePublic


def create_run_directory() -> Path:
    run_dir = TEMP_DIR / str(uuid4())
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_source_file(
    run_dir: Path,
    source_code: str,
    file_ext: str = ".py",
) -> Path:
    source_path = run_dir / f"main{file_ext}"
    source_path.write_text(source_code, encoding="utf-8")
    return source_path


def decode_output(data: bytes) -> tuple[str, bool]:
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return "", True


async def terminate_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        process.kill()
        await process.wait()


def cleanup_run_directory(run_dir: Path) -> None:
    shutil.rmtree(run_dir, ignore_errors=True)


def process_memory_bytes(process_id: int) -> int:
    try:
        process = psutil.Process(process_id)
        children = process.children(recursive=True)
        return process.memory_info().rss + sum(
            child.memory_info().rss for child in children if child.is_running()
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0


async def execute_process(
    command: list[str],
    input_bytes: bytes,
    time_limit: float,
    memory_limit: int,
    cwd: Path,
) -> ProcessRunResult:
    start_time = time.perf_counter()
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    communicate_task = asyncio.create_task(process.communicate(input_bytes))
    peak_memory = 0
    timed_out = False
    memory_exceeded = False
    memory_limit_bytes = memory_limit * 1024 * 1024

    while not communicate_task.done():
        elapsed = time.perf_counter() - start_time
        if elapsed > time_limit:
            timed_out = True
            await terminate_process(process)
            break
        current_memory = process_memory_bytes(process.pid)
        peak_memory = max(peak_memory, current_memory)
        if current_memory > memory_limit_bytes:
            memory_exceeded = True
            await terminate_process(process)
            break
        await asyncio.sleep(0.01)

    stdout_bytes, stderr_bytes = await communicate_task
    peak_memory = max(peak_memory, process_memory_bytes(process.pid))
    time_used = time.perf_counter() - start_time
    stdout, stdout_decode_error = decode_output(stdout_bytes)
    stderr, stderr_decode_error = decode_output(stderr_bytes)
    return ProcessRunResult(
        timed_out=timed_out,
        memory_exceeded=memory_exceeded,
        exit_code=process.returncode,
        time_used=time_used,
        memory_used=peak_memory // (1024 * 1024),
        stdout=stdout,
        stderr=stderr,
        decode_error=stdout_decode_error or stderr_decode_error,
    )


def format_command(
    template: str,
    source_path: Path,
    executable_path: Path,
) -> list[str]:
    command = template.format(
        src=str(source_path),
        exe=str(executable_path),
    )
    return shlex.split(command, posix=os.name != "nt")


async def run_language_case(
    source_code: str,
    input_data: str,
    time_limit: float,
    memory_limit: int,
    language: LanguagePublic,
) -> ProcessRunResult:
    run_dir: Path | None = None
    try:
        run_dir = create_run_directory()
        source_path = write_source_file(
            run_dir,
            source_code,
            language.file_ext,
        )
        executable_name = "program.exe" if os.name == "nt" else "program"
        executable_path = run_dir / executable_name

        if language.compile_cmd:
            compile_result = await execute_process(
                format_command(
                    language.compile_cmd,
                    source_path,
                    executable_path,
                ),
                b"",
                max(time_limit, 10.0),
                memory_limit,
                run_dir,
            )
            if (
                compile_result.exit_code != 0
                or compile_result.timed_out
                or compile_result.memory_exceeded
                or compile_result.decode_error
            ):
                compile_result.compile_error = True
                compile_result.compile_info = (
                    compile_result.stderr or compile_result.stdout
                )[:2000]
                return compile_result

        if language.name == "python":
            command = [sys.executable, str(source_path)]
        else:
            command = format_command(
                language.run_cmd,
                source_path,
                executable_path,
            )
        return await execute_process(
            command,
            input_data.encode("utf-8"),
            time_limit,
            memory_limit,
            run_dir,
        )
    except Exception as exc:
        return ProcessRunResult(system_error=type(exc).__name__)
    finally:
        if run_dir is not None:
            cleanup_run_directory(run_dir)
