import pytest


pytestmark = pytest.mark.skip(reason="submission management is not implemented yet")


def test_create_submission() -> None:
    """An authenticated user should be able to create a submission."""


def test_valid_status_transitions() -> None:
    """A submission should follow the valid status transition order."""


def test_invalid_status_transition_conflict() -> None:
    """An invalid status transition should return a conflict."""


def test_submission_ownership() -> None:
    """Students should only access submissions allowed by ownership rules."""


def test_rejudge_submission() -> None:
    """Teacher and admin users should be able to request rejudging."""
