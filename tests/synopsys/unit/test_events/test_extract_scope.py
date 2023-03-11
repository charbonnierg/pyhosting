import typing as t
from re import escape

import pytest

from synopsys import EMPTY, Event, create_event


@pytest.mark.parametrize(
    "subject,event,result",
    [
        ("test", create_event("test", "test", EMPTY), {}),
        ("test.someid", create_event("test", "test.{id}", EMPTY), {"id": "someid"}),
        (
            "test.someid.westus",
            create_event("test", "test.{device}.{location}", EMPTY),
            {"device": "someid", "location": "westus"},
        ),
    ],
)
def test_extract_subject_placeholders(
    subject: str, event: Event[t.Any, t.Any, t.Any], result: t.Dict[str, str]
):
    assert event.extract_scope(subject) == result


def test_extract_subject_placeholders_missing():
    event = create_event("test", "test.{device}", EMPTY)
    with pytest.raises(
        ValueError,
        match=escape("Invalid subject. Missing placeholder: device (index: 1)"),
    ):
        event.extract_scope("test")

    other_event = create_event("other", "other.{device}.{location}", EMPTY)
    with pytest.raises(
        ValueError,
        match=escape("Invalid subject. Missing placeholder: location (index: 2)"),
    ):
        other_event.extract_scope("other.device")
