import pytest


pytestmark = pytest.mark.skip(reason="automatic judging is not implemented yet")


def test_accepted_result() -> None:
    """Correct code should produce AC."""


def test_wrong_answer_result() -> None:
    """Incorrect output should produce WA."""


def test_runtime_error_result() -> None:
    """Runtime failures should produce RE."""


def test_time_limit_exceeded_result() -> None:
    """Timeouts should produce TLE."""


def test_multiple_test_cases() -> None:
    """The judge should execute every configured test case."""


def test_output_normalization() -> None:
    """Output comparison should apply the required normalization."""


def test_temporary_files_are_removed() -> None:
    """Judge temporary files should be removed after evaluation."""
