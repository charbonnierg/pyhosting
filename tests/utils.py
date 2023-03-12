import typing as t

import pytest

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
