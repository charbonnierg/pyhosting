from re import escape

import pytest
from typing_extensions import TypedDict

from synopsys import EMPTY, create_event


def test_event_empty_name():
    with pytest.raises(ValueError, match="Name cannot be empty"):
        create_event("", "address", EMPTY)


def test_event_empty_address():
    with pytest.raises(ValueError, match="Address cannot be empty"):
        create_event("name", "", EMPTY)


def test_event_repr():
    event = create_event("test", "test.event", EMPTY)
    assert repr(event) == "Event(name='test', address='test.event', schema=NoneType)"

    class Foo:
        pass

    other_event = create_event("test", "test.event", Foo)
    assert repr(other_event) == "Event(name='test', address='test.event', schema=Foo)"


def test_event_missing_scope_annotations():
    class EventScope(TypedDict):
        """A typed dict without the 'device' key which is required by the event."""

        location: str

    # Not OK using a typed dict with missing field
    with pytest.raises(
        ValueError,
        match=escape(
            "Too many placeholders in address or missing scope variables. Did not expect in address: ['device']"
        ),
    ):
        create_event("test", "test.{device}.{location}", schema=EMPTY, scope=EventScope)


def test_event_extra_scope_annotations():
    class EventScope(TypedDict):
        """A typed dict with an additional key 'location' not present in event address."""

        device: str
        location: str

    # Not OK using a typed dict with missing field
    with pytest.raises(
        ValueError,
        match=escape(
            "Not enough placeholders in address or unexpected scope variable. Missing in address: ['location']"
        ),
    ):
        create_event("test", "test.{device}", schema=EMPTY, scope=EventScope)


def test_event_proper_scope_annotations():
    class EventScope(TypedDict):
        """A typed dict with an additional key 'location' not present in event address."""

        device: str
        location: str

    event = create_event(
        "test", "test.{device}.{location}", schema=EMPTY, scope=EventScope
    )
    assert event.name == "test"
    assert event.scope == EventScope
    assert event.address == "test.{device}.{location}"
