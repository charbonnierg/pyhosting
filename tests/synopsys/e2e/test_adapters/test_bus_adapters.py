import typing as t

import pytest
from _pytest.fixtures import SubRequest

from synopsys import EventBus, Request, Responder, create_event
from synopsys.adapters.memory import InMemoryEventBus
from synopsys.adapters.nats import NATSEventBus
from synopsys.concurrency import Play, Waiter

ADAPTERS: t.Dict[str, t.Type[EventBus]] = {
    "memory": InMemoryEventBus,
    "nats": NATSEventBus,
}


@pytest.fixture
def bus(request: SubRequest) -> EventBus:
    """A fixture which returns an event bus."""
    param = getattr(request, "param", None)
    if param is None:
        kind = "memory"
        options = {}
    elif isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    return ADAPTERS[kind](**options)


@pytest.mark.asyncio
@pytest.mark.parametrize("bus", ["memory"], indirect=True)
class TestEventBusInterface:
    """Test the event bus interface."""

    async def test_event_bus_publish(self, bus: EventBus):
        event = create_event("test-event", "test", int)
        waiter = await Waiter.create(bus.subscribe(event))
        await bus.publish(event, None, 12, None)
        received_event = await waiter.wait()
        assert received_event.data == 12

    async def test_event_bus_observe_event(self, bus: EventBus):
        target_event = create_event("test-1", "test.1", int)
        ignored_event = create_event("test-2", "test.2", int)
        # Create a waiter
        waiter = await Waiter.create(bus.subscribe(target_event))
        # This event should be ignore
        await bus.publish(ignored_event, None, 0, None)
        # This event should be received
        await bus.publish(target_event, None, 12, None)
        received_event = await waiter.wait()
        assert received_event.data == 12

    async def test_event_bus_observe_event_variant(self, bus: EventBus):
        target_event = create_event("test-1", "test.*", int)
        ignored_event = create_event("other", "other.*", int)
        # Create a waiter
        waiter = await Waiter.create(bus.subscribe(target_event))
        # This event should be ignore
        await bus.publish(ignored_event, None, 0, None)
        # This event should be received
        await bus.publish(target_event, None, 12, None)
        received_event = await waiter.wait()
        assert received_event.data == 12

    async def test_event_bus_request(self, bus: EventBus):
        """Test case for request/reply.

        Given: An actor is created using an event and an event handler
        When: A play is created and started using the actor
        Then: Requesters can send messages and receive replies
        """
        event = create_event("test-command", "test", int, reply_schema=int)

        # Define an handler
        # Note that handler today requires 4 generic types...
        #  - The first one is the event scope (the data whind within message payload)
        #  - The third one is the event metadata (the data which can be found within message header)
        #  - The fourth one is the event reply (the data which is sent back as the reply ch can be found within subject)
        #  - The second one is the event payload (the data which can be foumessage payload)
        # I don't know how we can provide simpler API without sacrificing the ability to type messages.
        async def handler(request: Request[None, int, None, int]) -> int:
            """A test handler"""
            return request.data + 10

        actor = Responder(event, handler)
        # Use actors in order to start a service
        async with Play(bus, actors=[actor]) as play:
            # Once play is started
            # Requests can be sent and replied to
            reply = await bus.request(
                event,
                payload=12,
                scope=None,
                metadata=None,
                timeout=0.1,
            )
            # Should we distinguish cancel and drain ?
            # Cancelling should kill as soon as cancellation is requested
            # Draining should stop receiving new messages and wait until all
            # available messages are processed?
            play.cancel()

        assert reply == 22
