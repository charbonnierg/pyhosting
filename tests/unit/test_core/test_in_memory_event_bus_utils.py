import pytest

from pyhosting.core.adapters.bus import match_subject


@pytest.mark.parametrize(
    "subject,filter,match",
    [
        ("a", "a", True),
        ("ab", "*", True),
        ("ab", ">", True),
        ("ab.a", "ab.a", True),
        ("ab.a", "ab.*", True),
        ("a.b.c", "*.b.c", True),
        ("a.b.c", "a.*.c", True),
        ("a.b.c", "a.b.*", True),
        ("ab.a", ">", True),
        ("ab.a", "ab.>", True),
        ("a", "b", False),
        ("a.b", "*", False),
        ("a.a", "a.b", False),
        ("a.b.c", "a.*", False),
    ],
)
def test_match_subject(subject: str, filter: str, match: bool):
    assert match_subject(subject, filter) is match


def test_match_subject_error_subject_cannot_be_empty():
    with pytest.raises(ValueError, match="Subject cannot be empty"):
        match_subject("", "filter")


def test_match_subject_error_filter_cannot_be_empty():
    with pytest.raises(ValueError, match="Filter subject cannot be empty"):
        match_subject("subject", "")
