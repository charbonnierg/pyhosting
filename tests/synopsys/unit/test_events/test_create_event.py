from synopsys.core.api import create_event
from synopsys.core.events import EMPTY, Event, Service, StaticEvent, StaticService


def test_create_static_event() -> None:
    event = create_event(
        name="test",
        address="test.{device}",
        schema=int,
    )
    assert isinstance(event, StaticEvent)
    assert event.schema == int
    assert event.address == "test.{device}"
    assert event.name == "test"


def test_create_static_event_with_metadata() -> None:
    event = create_event(
        "test",
        "test.{device}",
        int,
        metadata_schema=dict,
    )
    assert isinstance(event, StaticEvent)
    assert event.metadata_schema == dict
    assert event.schema == int
    assert event.scope == EMPTY
    assert event.reply_schema == EMPTY


def test_create_event_with_scope() -> None:
    event = create_event(
        name="test",
        address="test.{device}",
        schema=int,
        scope=dict,
    )
    assert isinstance(event, Event)
    assert event.schema == int
    assert event.scope == dict
    assert event.metadata_schema == EMPTY
    assert event.reply_schema == EMPTY


def test_create_event_with_scope_and_metadata() -> None:
    event = create_event(
        name="test",
        address="test.{device}",
        schema=int,
        scope=dict,
        metadata_schema=dict,
    )
    assert isinstance(event, Event)
    assert event.schema == int
    assert event.scope == dict
    assert event.metadata_schema == dict
    assert event.reply_schema == EMPTY


def test_create_service_with_scope() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=float,
        scope=dict,
    )
    assert isinstance(event, Service)
    assert event.schema == int
    assert event.scope == dict
    assert event.reply_schema == float
    assert event.metadata_schema == EMPTY


def test_create_service_with_scope_reply_none() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=EMPTY,
        scope=dict,
    )
    assert isinstance(event, Service)
    assert event.schema == int
    assert event.scope == dict
    assert event.reply_schema == EMPTY
    assert event.metadata_schema == EMPTY


def test_create_static_service_with_metadata() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=float,
        metadata_schema=dict,
    )
    assert isinstance(event, StaticService)
    assert event.schema == int
    assert event.scope == EMPTY
    assert event.reply_schema == float
    assert event.metadata_schema == dict


def test_create_static_service_with_metadata_reply_none() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=EMPTY,
        metadata_schema=dict,
    )
    assert isinstance(event, StaticService)
    assert event.schema == int
    assert event.scope == EMPTY
    assert event.reply_schema == EMPTY
    assert event.metadata_schema == dict


def test_create_service_with_scope_and_metata() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=float,
        scope=dict,
        metadata_schema=dict,
    )
    assert isinstance(event, Service)
    assert event.schema == int
    assert event.scope == dict
    assert event.reply_schema == float
    assert event.metadata_schema == dict


def test_create_service_with_scope_and_metata_reply_none() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=EMPTY,
        scope=dict,
        metadata_schema=dict,
    )
    assert isinstance(event, Service)
    assert event.schema == int
    assert event.scope == dict
    assert event.reply_schema == EMPTY
    assert event.metadata_schema == dict


def test_create_static_service() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=float,
    )
    assert isinstance(event, StaticService)
    assert event.schema == int
    assert event.reply_schema == float
    assert event.scope == EMPTY
    assert event.metadata_schema == EMPTY


def test_create_static_service_reply_none() -> None:
    event = create_event(
        "test-service",
        "test.service",
        schema=int,
        reply_schema=EMPTY,
    )
    assert isinstance(event, StaticService)
    assert event.schema == int
    assert event.reply_schema == EMPTY
    assert event.scope == EMPTY
    assert event.metadata_schema == EMPTY
