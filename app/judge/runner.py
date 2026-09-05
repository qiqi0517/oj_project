import asyncio
import logging
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from string import Formatter
from typing import Any
from uuid import uuid4

import psutil

from app.config import TEMP_DIR
from app.models.judge import ProcessRunResult
from app.models.language import LanguagePublic

PYTHON_RUN_COMMAND = f'"{sys.executable}" {{src}}'
logger = logging.getLogger(__name__)


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


def bytes_to_mebibytes_rounded_up(byte_count: int) -> int:
    mebibyte = 1024 * 1024
    return (byte_count + mebibyte - 1) // mebibyte


def track_process_tree(
    process_id: int,
    tracked_processes: dict[int, psutil.Process],
) -> None:
    try:
        root_process = psutil.Process(process_id)
        processes = [root_process, *root_process.children(recursive=True)]
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return
    for process in processes:
        tracked_processes[process.pid] = process


def find_orphaned_children(
    process_id: int,
    tracked_processes: dict[int, psutil.Process],
) -> None:
    parent_ids = {process_id, *tracked_processes}
    for _ in range(3):
        found_child = False
        for process in psutil.process_iter(["pid", "ppid"]):
            try:
                if (
                    process.info["ppid"] in parent_ids
                    and process.pid not in tracked_processes
                ):
                    tracked_processes[process.pid] = process
                    parent_ids.add(process.pid)
                    found_child = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not found_child:
            break


def kill_tracked_processes(processes: list[psutil.Process]) -> None:
    for process in reversed(processes):
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    _, alive = psutil.wait_procs(processes, timeout=1.0)
    for process in alive:
        try:
            process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if alive:
        psutil.wait_procs(alive, timeout=1.0)


async def terminate_process_tree(
    process: asyncio.subprocess.Process,
    tracked_processes: dict[int, psutil.Process],
) -> None:
    track_process_tree(process.pid, tracked_processes)
    find_orphaned_children(process.pid, tracked_processes)
    if os.name != "nt":
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    await asyncio.to_thread(
        kill_tracked_processes,
        [
            tracked_process
            for tracked_process in tracked_processes.values()
            if tracked_process.pid != process.pid
        ],
    )
    if process.returncode is None:
        with suppress(ProcessLookupError):
            process.kill()
    await process.wait()


def cleanup_run_directory(run_dir: Path) -> None:
    shutil.rmtree(run_dir, ignore_errors=True)


def process_memory_bytes(
    process_id: int,
    tracked_processes: dict[int, psutil.Process] | None = None,
) -> int:
    if tracked_processes is None:
        tracked_processes = {}
    track_process_tree(process_id, tracked_processes)
    total_memory = 0
    for process in tracked_processes.values():
        try:
            if process.is_running():
                total_memory += process.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total_memory


def terminate_popen_tree(
    process: subprocess.Popen[bytes],
    tracked_processes: dict[int, psutil.Process],
) -> None:
    """Terminate a synchronous subprocess and every child it created."""
    track_process_tree(process.pid, tracked_processes)
    find_orphaned_children(process.pid, tracked_processes)
    kill_tracked_processes(
        [
            tracked_process
            for tracked_process in tracked_processes.values()
            if tracked_process.pid != process.pid
        ]
    )
    if process.poll() is None:
        with suppress(ProcessLookupError, OSError):
            process.kill()
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError, OSError):
            process.kill()
        process.wait()


def execute_process_windows(
    command: list[str],
    input_bytes: bytes,
    time_limit: float,
    memory_limit: int,
    cwd: Path,
) -> ProcessRunResult:
    """Run a judge process without relying on asyncio subprocess support.

    Uvicorn can use a Windows selector event loop, notably in reload mode. That
    loop deliberately does not implement subprocess transports. Running the
    blocking subprocess supervisor in an asyncio worker thread keeps judging
    compatible with either Windows event-loop implementation.
    """
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    start_time = time.perf_counter()
    tracked_processes: dict[int, psutil.Process] = {}
    track_process_tree(process.pid, tracked_processes)
    peak_memory = 0
    timed_out = False
    memory_exceeded = False
    memory_limit_bytes = memory_limit * 1024 * 1024
    pending_input: bytes | None = input_bytes
    stdout_bytes = b""
    stderr_bytes = b""

    try:
        while True:
            try:
                stdout_bytes, stderr_bytes = process.communicate(
                    pending_input,
                    timeout=0.01,
                )
                break
            except subprocess.TimeoutExpired:
                pending_input = None

            elapsed = time.perf_counter() - start_time
            current_memory = process_memory_bytes(
                process.pid,
                tracked_processes,
            )
            peak_memory = max(peak_memory, current_memory)
            if elapsed > time_limit:
                timed_out = process.poll() is None
                terminate_popen_tree(process, tracked_processes)
                stdout_bytes, stderr_bytes = process.communicate()
                break
            if current_memory > memory_limit_bytes:
                memory_exceeded = True
                terminate_popen_tree(process, tracked_processes)
                stdout_bytes, stderr_bytes = process.communicate()
                break

        peak_memory = max(
            peak_memory,
            process_memory_bytes(process.pid, tracked_processes),
        )
        time_used = time.perf_counter() - start_time
    finally:
        terminate_popen_tree(process, tracked_processes)

    stdout, stdout_decode_error = decode_output(stdout_bytes)
    stderr, stderr_decode_error = decode_output(stderr_bytes)
    return ProcessRunResult(
        timed_out=timed_out,
        memory_exceeded=memory_exceeded,
        exit_code=process.returncode,
        time_used=time_used,
        memory_used=bytes_to_mebibytes_rounded_up(peak_memory),
        stdout=stdout,
        stderr=stderr,
        decode_error=stdout_decode_error or stderr_decode_error,
    )


async def execute_process(
    command: list[str],
    input_bytes: bytes,
    time_limit: float,
    memory_limit: int,
    cwd: Path,
) -> ProcessRunResult:
    if os.name == "nt":
        return await asyncio.to_thread(
            execute_process_windows,
            command,
            input_bytes,
            time_limit,
            memory_limit,
            cwd,
        )

    process_options: dict[str, Any] = {"start_new_session": True}
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        **process_options,
    )
    start_time = time.perf_counter()
    communicate_task = asyncio.create_task(process.communicate(input_bytes))
    tracked_processes: dict[int, psutil.Process] = {}
    track_process_tree(process.pid, tracked_processes)
    peak_memory = 0
    timed_out = False
    memory_exceeded = False
    memory_limit_bytes = memory_limit * 1024 * 1024

    try:
        while not communicate_task.done():
            elapsed = time.perf_counter() - start_time
            if elapsed > time_limit:
                timed_out = process.returncode is None
                await terminate_process_tree(process, tracked_processes)
                break
            current_memory = process_memory_bytes(
                process.pid,
                tracked_processes,
            )
            peak_memory = max(peak_memory, current_memory)
            if current_memory > memory_limit_bytes:
                memory_exceeded = True
                await terminate_process_tree(process, tracked_processes)
                break
            await asyncio.sleep(0.01)

        stdout_bytes, stderr_bytes = await communicate_task
        peak_memory = max(
            peak_memory,
            process_memory_bytes(process.pid, tracked_processes),
        )
        time_used = time.perf_counter() - start_time
    finally:
        await terminate_process_tree(process, tracked_processes)
    stdout, stdout_decode_error = decode_output(stdout_bytes)
    stderr, stderr_decode_error = decode_output(stderr_bytes)
    return ProcessRunResult(
        timed_out=timed_out,
        memory_exceeded=memory_exceeded,
        exit_code=process.returncode,
        time_used=time_used,
        memory_used=bytes_to_mebibytes_rounded_up(peak_memory),
        stdout=stdout,
        stderr=stderr,
        decode_error=stdout_decode_error or stderr_decode_error,
    )


def split_command_template(template: str) -> list[str]:
    parts = shlex.split(template, posix=os.name != "nt")
    if os.name == "nt":
        parts = [
            part[1:-1]
            if len(part) >= 2 and part[0] == part[-1] and part[0] in "\"'"
            else part
            for part in parts
        ]
    return parts


def command_placeholders(template: str) -> set[str]:
    placeholders: set[str] = set()
    for _, field_name, format_spec, conversion in Formatter().parse(template):
        if format_spec or conversion:
            raise ValueError("language command cannot format placeholders")
        if field_name is not None:
            placeholders.add(field_name)
    return placeholders


def validate_language_commands(
    compile_cmd: str | None,
    run_cmd: str,
) -> None:
    templates = [run_cmd]
    if compile_cmd is not None:
        templates.append(compile_cmd)
    for template in templates:
        if not template.strip():
            raise ValueError("language command cannot be empty")
        if not split_command_template(template):
            raise ValueError("language command cannot be empty")
        if not command_placeholders(template) <= {"src", "exe"}:
            raise ValueError("language command contains unsupported placeholders")


def format_command(
    template: str,
    source_path: Path,
    executable_path: Path,
) -> list[str]:
    return [
        part.format(src=str(source_path), exe=str(executable_path))
        for part in split_command_template(template)
    ]


async def run_language_case(
    source_code: str,
    input_data: str,
    time_limit: float,
    memory_limit: int,
    language: LanguagePublic,
) -> ProcessRunResult:
    run_dir: Path | None = None
    stage = "validating language command"
    try:
        validate_language_commands(language.compile_cmd, language.run_cmd)
        stage = "creating run directory"
        run_dir = create_run_directory()
        stage = "writing source file"
        source_path = write_source_file(
            run_dir,
            source_code,
            language.file_ext,
        )
        executable_name = "program.exe" if os.name == "nt" else "program"
        executable_path = run_dir / executable_name

        if language.compile_cmd:
            stage = "compiling source"
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
                if compile_result.timed_out:
                    compile_output = "compilation timed out"
                elif compile_result.memory_exceeded:
                    compile_output = "compilation memory limit exceeded"
                elif compile_result.decode_error:
                    compile_output = "compiler output is not valid UTF-8"
                else:
                    compile_output = (
                        compile_result.stderr
                        or compile_result.stdout
                        or "compilation failed"
                    )
                compile_result.compile_info = compile_output.replace(
                    str(run_dir),
                    ".",
                )[:2000]
                return compile_result

        command = format_command(
            language.run_cmd,
            source_path,
            executable_path,
        )
        stage = "running program"
        return await execute_process(
            command,
            input_data.encode("utf-8"),
            time_limit,
            memory_limit,
            run_dir,
        )
    except Exception as exc:
        error_name = type(exc).__name__
        logger.exception(
            "Judge runner failed while %s (language=%s)",
            stage,
            language.name,
        )
        return ProcessRunResult(system_error=f"{error_name}: {exc}")
    finally:
        if run_dir is not None:
            cleanup_run_directory(run_dir)
