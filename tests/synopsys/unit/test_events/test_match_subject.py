import pytest

from synopsys import EMPTY, create_event


@pytest.mark.parametrize(
    "subject,address,match",
    [
        ("a", "a", True),
        ("ab", "{device}", True),
        ("ab.a", "ab.a", True),
        # ("ab.a", "{...parts}", True),
        ("ab.a", "ab.{device}", True),
        ("a.b.c", "{device}.b.c", True),
        ("a.b.c", "a.{device}.c", True),
        ("a.b.c", "a.b.{device}", True),
        # ("ab.a", "{device}.{...parts}", True),
        ("a", "b", False),
        ("a.b", "{device}", False),
        ("a.a", "a.b", False),
        ("a.b.c", "a.{device}", False),
        ("a", "a.b", False),
        ("a", "a.{device}", False),
        # ("a", "a.{...parts}", False),
    ],
)
def test_match_subject(subject: str, address: str, match: bool):
    assert (
        create_event("test", address, EMPTY, scope=dict).match_subject(subject) is match
    )


def test_match_subject_error_filter_subject_cannot_be_empty():
    event = create_event("test", "test", EMPTY, scope=dict)
    with pytest.raises(ValueError, match="Subject cannot be empty"):
        event.match_subject("")
