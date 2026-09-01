from pathlib import Path
from uuid import uuid4

from app.config import TEMP_DIR


def create_run_directory() -> Path:
    run_dir = TEMP_DIR / str(uuid4())
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def write_source_file(run_dir: Path, source_code: str) -> Path:
    source_path = run_dir / "main.py"
    source_path.write_text(source_code, encoding="utf-8")
    return source_path