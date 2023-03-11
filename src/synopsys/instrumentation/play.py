import typing as t
from dataclasses import dataclass

from ..core.interfaces import BaseMessage

if t.TYPE_CHECKING:
    from ..concurrency.play import Play

T = t.TypeVar("T")


class Actor(t.Generic[T]):
    pass


@dataclass
class PlayInstrumentation:
    """Configure how a play should be instrumented."""

    actor_started: t.Callable[[Actor[t.Any]], None] = lambda _: None
    """Observe actor started."""

    actor_cancelled: t.Callable[[Actor[t.Any]], None] = lambda _: None
    """Observe actor being cancelled."""

    actor_failed: t.Callable[
        [Actor[t.Any], BaseMessage[t.Any, t.Any, t.Any, t.Any], BaseException], None
    ] = lambda _, __, ___: None
    """Observe an exception raised by an actor."""

    event_processed: t.Callable[
        [Actor[t.Any], BaseMessage[t.Any, t.Any, t.Any, t.Any]], None
    ] = lambda _, __: None
    """Observe a successful command processed"""

    play_starting: t.Callable[["Play"], None] = lambda _: None
    """Observe play starting."""

    play_started: t.Callable[["Play"], None] = lambda _: None
    """Observe play started."""

    play_stopping: t.Callable[["Play"], None] = lambda _: None
    """Observe play stopping."""

    play_failed: t.Callable[["Play", t.List[BaseException]], None] = lambda _, __: None
    """Observe actors play failure"""

    play_stopped: t.Callable[["Play"], None] = lambda _: None
    """Observe actors play stopped"""
