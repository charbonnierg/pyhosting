"""An event is an abstraction representing some data, on a given address.

For example, a usecase where data measured by sensors must be sent accross the network can
be modelized using the following event:

```python
from dataclasses import dataclass


@dataclass
class SensorData:
    timestamp: int
    value: float
    unit: str


MEASUREMENTS = Event(
    title="measurements",
    address="devices.{device_id}.{location}.measurement",
    schema=SensorData,
    description="Some measurement",
)
```

Then it will be possible to emit or observe typed messages on an event bus:

```python
from pyhosting.core import EventBus

class Publisher:

    # Reuse the event defined above
    event = MEASUREMENTS

    def __init__(self, bus: EventBus, location: str) -> None:
        self.bus = bus
        self.location = location

    async def publish(self, device_id: str, value: float, unit: str, timestamp: int) -> None
        \"\"\"Publish an event\"\"\"
        # In order to publish an event
        # Additional kwargs may be required
        # (depending on the event address)
        await self.bus.publish(
            event=self.event,
            data=SensorData(
                value=value,
                unit=unit,
                timestamp=timestamp,
            ),
            device_id=device_id,
            location=self.location,
        )

```

Obsevers on the other hand can subscribe to all or only a subject of events:

```python

```

"""
import typing as t

from ..utils.events import render_subject
from .subjects import Filter, FilterSyntax

DataT = t.TypeVar("DataT")
ResultT = t.TypeVar("ResultT")
ScopeT = t.TypeVar("ScopeT", bound=t.Mapping[str, t.Any])


class NO_PARAM(t.TypedDict):  # NOSONAR[python:S101]
    pass


class EventSpec(t.Generic[ScopeT, DataT]):
    """An event is the combination of a subject and a schema."""

    name: str
    """The event name."""

    address: str
    """The event address. Similar to NATS subjects, MQTT topics, or Kafka topics."""

    schema: t.Type[DataT]
    """The event schema, I.E, the schema of the data found in event messages."""

    scope: t.Type[ScopeT]
    """The parameters used to construct a valid event address."""

    title: str
    """The event title."""

    description: str
    """A short description for the event."""

    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        scope: t.Type[ScopeT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        """Create a new event using a subjet and a schema."""
        if not name:
            raise ValueError("Name cannot be empty")
        if not address:
            raise ValueError("Address cannot be empty")
        self.name = name
        self.address = address
        self.schema = schema
        self.scope = scope
        self.title = title or name
        self.description = description or ""
        # Save filter to easily match or extract subjects
        self.filter = Filter(address, syntax=syntax)
        # Validate the address
        if not hasattr(self.scope, "__annotations__"):
            # Do not validate if scope does not have annotation
            return
        if len(self.scope.__annotations__) > len(self.filter._placeholders):
            missing = list(
                set(self.scope.__annotations__).difference(self.filter._placeholders)
            )
            raise ValueError(f"Not enough placeholders in address. Missing: {missing}")
        if len(self.scope.__annotations__) < len(self.filter._placeholders):
            unexpected = list(
                set(self.filter._placeholders).difference(self.scope.__annotations__)
            )
            raise ValueError(
                f"Too many placeholders in address or missing type annotations for scope. Did not expect: {unexpected}"
            )

    def __repr__(self) -> str:
        return f"Event(address={self.address}, schema={self.schema.__name__})"

    def match_subject(self, subject: str) -> bool:
        """Return True if event matches given subject."""
        return self.filter.match(subject)

    def extract_scope(self, subject: str) -> ScopeT:
        """Extract placeholders from subject"""
        return t.cast(ScopeT, self.filter.extract(subject))

    def get_subject(self, params: ScopeT) -> str:
        """Get a subject matching the filter."""
        return render_subject(
            tokens=self.filter._tokens,
            placeholders=self.filter._placeholders,
            context=dict(params) if params else {},
            syntax=self.filter.syntax,
        )


class Event(EventSpec[ScopeT, DataT]):
    pass


class StaticEvent(Event[NO_PARAM, DataT]):
    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name=name,
            address=address,
            schema=schema,
            scope=NO_PARAM,
            title=title,
            description=description,
            syntax=syntax,
        )

    def get_subject(self, params: t.Optional[NO_PARAM] = None) -> str:
        return super().get_subject(NO_PARAM())


class Command(EventSpec[ScopeT, DataT], t.Generic[ScopeT, DataT, ResultT]):
    reply_schema: t.Type[ResultT]
    """The result schema, I.E, the schema of the result of event processing."""

    reply_description: str
    """Desceiption of the reply content"""

    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        scope: t.Type[ScopeT],
        reply_schema: t.Type[ResultT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        reply_description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name=name,
            address=address,
            schema=schema,
            scope=scope,
            title=title,
            description=description,
            syntax=syntax,
        )
        self.reply_schema = reply_schema
        self.reply_description = reply_description or ""


class StaticCommand(Command[NO_PARAM, DataT, ResultT]):
    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        reply_schema: t.Type[ResultT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        reply_description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name=name,
            address=address,
            schema=schema,
            scope=NO_PARAM,
            title=title,
            description=description,
            reply_schema=reply_schema,
            reply_description=reply_description,
            syntax=syntax,
        )


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Type[ScopeT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Event[ScopeT, DataT]:
    ...


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticEvent[DataT]:
    ...


def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Optional[t.Type[t.Any]] = None,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Event[t.Any, DataT]:
    if scope:
        return Event(
            name=name,
            address=address,
            schema=schema,
            scope=scope,
            title=title,
            description=description,
            syntax=syntax,
        )
    return StaticEvent(
        name=name,
        address=address,
        schema=schema,
        title=title,
        description=description,
        syntax=syntax,
    )


@t.overload
def create_command(
    name: str,
    address: str,
    schema: t.Type[DataT],
    reply_schema: t.Type[ResultT],
    *,
    description: t.Optional[str] = None,
    reply_description: t.Optional[str] = None,
    scope: t.Type[ScopeT],
    syntax: t.Optional[FilterSyntax] = None,
) -> Command[ScopeT, DataT, ResultT]:
    ...


@t.overload
def create_command(
    name: str,
    address: str,
    schema: t.Type[DataT],
    reply_schema: None,
    *,
    scope: t.Type[ScopeT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    reply_description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Command[ScopeT, DataT, None]:
    ...


@t.overload
def create_command(
    name: str,
    address: str,
    schema: t.Type[DataT],
    reply_schema: t.Type[ResultT],
    *,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    reply_description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticCommand[DataT, ResultT]:
    ...


@t.overload
def create_command(
    name: str,
    address: str,
    schema: t.Type[DataT],
    reply_schema: None,
    *,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    reply_description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticCommand[DataT, None]:
    ...


def create_command(
    name: str,
    address: str,
    schema: t.Type[DataT],
    reply_schema: t.Any,
    *,
    scope: t.Optional[t.Type[t.Any]] = None,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    reply_description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Command[t.Any, DataT, t.Any]:
    if scope:
        return Command(
            name=name,
            address=address,
            schema=schema,
            scope=scope,
            title=title,
            description=description,
            reply_schema=reply_schema,
            reply_description=reply_description,
            syntax=syntax,
        )
    return StaticCommand(
        name=name,
        address=address,
        schema=schema,
        title=title,
        description=description,
        reply_schema=reply_schema,
        reply_description=reply_description,
        syntax=syntax,
    )


class DeviceScope(t.TypedDict):
    device_id: str
    location: str


class Measurement:
    value: float
    unit: str


# Create an event without parameter
evt = create_event(
    "measurement",
    address="{env}.measurement",
    schema=Measurement,
    scope=t.Dict[str, str],
)

# Create an event with parameters
evt2 = create_event(
    "measurement",
    address="test.{device}.{location}",
    schema=Measurement,
    scope=DeviceScope,
)


class CmdOptions:
    pass


class CmdResult:
    pass


cmd = create_command(
    "test-command", "test.command.{device_id}.{location}", int, float, scope=DeviceScope
)

cmd2 = create_command("test-command-2", "test.command.2", int, None)
