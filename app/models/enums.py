from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    BANNED = "banned"


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


class JudgeResult(str, Enum):
    AC = "AC"
    WA = "WA"
    TLE = "TLE"
    MLE = "MLE"
    RE = "RE"
    CE = "CE"
    UNK = "UNK"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
