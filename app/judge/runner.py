import asyncio
import sys
import time
import shutil
from pathlib import Path
from uuid import uuid4

from app.config import TEMP_DIR
from app.models.judge import ProcessRunResult


def create_run_directory() -> Path:
    run_dir = TEMP_DIR / str(uuid4())
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_source_file(run_dir: Path, source_code: str) -> Path:
    source_path = run_dir / "main.py"
    source_path.write_text(source_code, encoding="utf-8")
    return source_path


def decode_output(data: bytes) -> tuple[str, bool]:
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return "", True


async def terminate_process(
    process: asyncio.subprocess.Process,
) -> None:
    if process.returncode is None:
        process.kill()
        await process.wait()


def cleanup_run_directory(run_dir: Path) -> None:
    shutil.rmtree(run_dir, ignore_errors=True)


async def run_python_case(
    source_code: str,
    input_data: str,
    time_limit: float,
) -> ProcessRunResult:
    process: asyncio.subprocess.Process | None = None
    run_dir: Path | None = None
    start_time: float | None = None
    try:
        run_dir = create_run_directory()
        source_path = write_source_file(run_dir, source_code)
        input_bytes = input_data.encode("utf-8")
        start_time = time.perf_counter()
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(source_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=run_dir,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input_bytes),
                timeout=time_limit,
            )
        except asyncio.TimeoutError:
            await terminate_process(process)
            time_used = time.perf_counter() - start_time
            return ProcessRunResult(
                timed_out=True,
                exit_code=process.returncode,
                time_used=time_used,
            )
        time_used = time.perf_counter() - start_time
        stdout, stdout_decode_error = decode_output(stdout_bytes)
        stderr, stderr_decode_error = decode_output(stderr_bytes)
        return ProcessRunResult(
            exit_code=process.returncode,
            time_used=time_used,
            stdout=stdout,
            stderr=stderr,
            decode_error=stdout_decode_error or stderr_decode_error,
        )
    except Exception as exc:
        if process is not None:
            await terminate_process(process)
        if start_time is None:
            time_used = 0.0
        else:
            time_used = time.perf_counter() - start_time
        return ProcessRunResult(
            time_used=time_used,
            system_error=type(exc).__name__,
        )
    finally:
        if run_dir is not None:
            cleanup_run_directory(run_dir)
