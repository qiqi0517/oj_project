from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import aiosqlite
from app.config import DATABASE_PATH


# create database tables
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_PROBLEMS_TABLE = """
CREATE TABLE IF NOT EXISTS problems (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    input_description TEXT NOT NULL,
    output_description TEXT NOT NULL,
    constraints TEXT NOT NULL,
    time_limit REAL NOT NULL,
    memory_limit INTEGER NOT NULL,
    difficulty TEXT NOT NULL,
    tags TEXT NOT NULL,
    samples TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_TEST_CASES_TABLE = """
CREATE TABLE IF NOT EXISTS test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    input_data TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    score INTEGER NOT NULL,
    is_hidden INTEGER NOT NULL DEFAULT 0,

    UNIQUE(problem_id, case_id),

    FOREIGN KEY (problem_id)
        REFERENCES problems(id)
        ON DELETE CASCADE
);
"""

CREATE_SUBMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    language TEXT NOT NULL,
    source_code TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    score INTEGER NOT NULL DEFAULT 0,
    total_time REAL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
);
"""

CREATE_JUDGE_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS judge_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    result TEXT NOT NULL,
    score INTEGER NOT NULL,
    time_used REAL NOT NULL,
    memory_used INTEGER,
    exit_code INTEGER,
    input_data TEXT NOT NULL,
    stdout TEXT NOT NULL,
    stderr TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    message TEXT,
    is_hidden INTEGER NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (submission_id)
        REFERENCES submissions(id)
        ON DELETE CASCADE
);
"""

CREATE_AUDIT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    success INTEGER NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (operator_id)
        REFERENCES users(id)
);
"""

CREATE_BACKUPS_TABLE = """
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    storage_type TEXT NOT NULL,
    path TEXT NOT NULL
);
"""

CREATE_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_PROBLEMS_TABLE,
    CREATE_TEST_CASES_TABLE,
    CREATE_SUBMISSIONS_TABLE,
    CREATE_JUDGE_LOGS_TABLE,
    CREATE_AUDIT_LOGS_TABLE,
    CREATE_BACKUPS_TABLE,
]



# general database connecter
@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # make sql query output in the form of aiosqlite.Row
        db.row_factory = aiosqlite.Row
        # enable Foreign Key in database
        await db.execute("PRAGMA foreign_keys = ON")
        # when complete db execution, 'yield' ensures get_db_connections exucute on and close
        yield db


# init database
async def init_database() -> None:
    async with get_db_connection() as db:
        # create tables
        for create_table in CREATE_TABLES:
            await db.execute(create_table)
        # commit
        await db.commit()
