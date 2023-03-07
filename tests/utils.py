import asyncio
import typing as t

import pytest

from pyhosting.domain.gateways.event_bus import EventBusGateway

F = t.TypeVar("F", bound=t.Callable[..., t.Any])
T = t.TypeVar("T")


def parametrize_id_generator(kind: str, **kwargs: t.Any) -> t.Callable[[F], F]:
    """A decorator to parametrize id_generator fixture."""

    def decorator(func: F) -> F:
        return t.cast(
            F,
            pytest.mark.parametrize(
                "id_generator",
                [(kind, kwargs)],
                ids=["id/" + kind],
                indirect=True,
            )(func),
        )

    return decorator


def parametrize_event_bus(kind: str, **kwargs: t.Any) -> t.Callable[[F], F]:
    """A decorator to parametrize event_bus fixture."""

    def decorator(func: F) -> F:
        return t.cast(
            F,
            pytest.mark.parametrize(
                "event_bus",
                [(kind, kwargs)],
                ids=["eventbus/" + kind],
                indirect=True,
            )(func),
        )

    return decorator


def parametrize_page_repository(kind: str, **kwargs: t.Any) -> t.Callable[[F], F]:
    """A decorator to parametrize page_repository fixture."""

    def decorator(func: F) -> F:
        return t.cast(
            F,
            pytest.mark.parametrize(
                "page_repository",
                [(kind, kwargs)],
                ids=["pagerepo/" + kind],
                indirect=True,
            )(func),
        )

    return decorator


def parametrize_page_version_repository(
    kind: str, **kwargs: t.Any
) -> t.Callable[[F], F]:
    """A decorator to parametrize version_repository fixture."""

    def decorator(func: F) -> F:
        return t.cast(
            F,
            pytest.mark.parametrize(
                "version_repository",
                [(kind, kwargs)],
                ids=["pageversionrepo/" + kind],
                indirect=True,
            )(func),
        )

    return decorator


def parametrize_clock(clock: t.Callable[[], int]) -> t.Callable[[F], F]:
    """A decorator to parametrize clock fixture."""

    def decorator(func: F) -> F:
        return t.cast(
            F,
            pytest.mark.parametrize(
                "clock",
                [clock],
                ids=["clock"],
                indirect=True,
            )(func),
        )

    return decorator


class Waiter(t.Generic[T]):
    def __init__(self, bus: EventBusGateway, event: t.Tuple[str, t.Type[T]]) -> None:
        self.event = event
        self.bus = bus
        self.task = asyncio.create_task(bus.wait_for_event(event))

    @classmethod
    async def start_in_background(
        cls, bus: EventBusGateway, event: t.Tuple[str, t.Type[T]]
    ) -> "Waiter[T]":
        waiter = cls(bus, event)
        await asyncio.sleep(0)
        return waiter

    async def wait(self, timeout: t.Optional[float] = 5) -> T:
        return await asyncio.wait_for(self.task, timeout=timeout)
