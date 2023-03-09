import pytest
from _pytest.fixtures import SubRequest

from pyhosting.core.adapters import InMemoryEventBus
from pyhosting.core.aio import Actors
from pyhosting.core.entities import Command, Event, Filter, Service
from pyhosting.core.interfaces import EventBus, Request
from tests.utils import Waiter


@pytest.fixture
def bus(request: SubRequest) -> EventBus:
    """A fixture which returns an event bus.

    Fixture could be parametrized in the fixture in order to accept more event bus.
    """
    param = getattr(request, "param", None)
    if param is None:
        kind = "memory"
        options = {}
    elif isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    kinds = {"memory": InMemoryEventBus}
    return kinds[kind](**options)


@pytest.mark.asyncio
@pytest.mark.parametrize("bus", ["memory"], indirect=True)
class TestEventBusInterface:
    """Test the event bus interface."""

    async def test_event_bus_publish(self, bus: EventBus):
        event = Event("test-event", int)
        waiter = await Waiter.create(bus, event)
        await bus.publish(event, 12)
        received_event = await waiter.wait()
        assert received_event == 12

    async def test_event_bus_request(self, bus: EventBus):
        command = Command("test-command", int, int)

        async def handler(request: Request[int, int]) -> int:
            return 12

        service = Service(command, handler=handler)

        # Use actors in order to start a service
        async with Actors(bus, actors=[service]) as group:
            reply = await bus.request(command, 12, timeout=0.1)
            group.cancel()

        assert reply == 12

    async def test_event_bus_observe_event(self, bus: EventBus):
        target_event = Event("test.1", int)
        ignored_event = Event("something-else", int)
        waiter = await Waiter.create(bus, target_event)
        # This event should be ignore
        await bus.publish(ignored_event, 0)
        # This event should be received
        await bus.publish(target_event, 12)
        received_event = await waiter.wait()
        assert received_event == 12

    async def test_event_bus_observe_filter(self, bus: EventBus):
        target_events = Filter("test.*", int)
        ignored_event = Event("something-else", int)
        waiter = await Waiter.create(bus, target_events)
        # This event should be ignore
        await bus.publish(ignored_event, 0)
        # This event should be received
        await bus.publish(Event("test.1", int), 12)
        received_event = await waiter.wait()
        assert received_event == 12
