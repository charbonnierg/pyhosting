import typing as t
from re import escape

import pytest

from synopsys import EMPTY, create_event


@pytest.mark.parametrize(
    "address,scope,result",
    [
        ("test", {}, "test"),
        ("test", {"extra": "ignored"}, "test"),
        ("test.{device}", {"device": "XXX"}, "test.XXX"),
        (
            "test.{device}.{location}",
            {"device": "XXX", "location": "westus"},
            "test.XXX.westus",
        ),
    ],
)
def test_get_subject(
    address: str,
    scope: t.Dict[str, str],
    result: str,
):
    assert create_event("test", address, EMPTY, scope=dict).get_subject(scope) == result


def test_get_subject_missing_single_placeholder():
    event = create_event("test", "test.{device}", EMPTY, scope=dict)
    with pytest.raises(
        ValueError,
        match=escape("Cannot render subject. Missing placeholders: ['device']"),
    ):
        event.get_subject({})


def test_get_subject_missing_several_placeholders():
    event = create_event("test", "test.{device}.{location}", EMPTY, scope=dict)
    with pytest.raises(
        ValueError,
        match=escape(
            "Cannot render subject. Missing placeholders: ['device', 'location']"
        ),
    ):
        event.get_subject({})


def test_get_subject_static_event():
    evt = create_event("test", "test", EMPTY)
    assert evt.get_subject() == "test"


def test_render_subject_static_event():
    evt = create_event("test", "test", EMPTY, reply_schema=EMPTY)
    assert evt.get_subject() == "test"
