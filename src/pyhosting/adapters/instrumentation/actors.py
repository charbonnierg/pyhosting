import logging
import typing as t

from synopsys.concurrency import Play
from synopsys.core.actors import Actor
from synopsys.core.interfaces import BaseMessage
from synopsys.instrumentation.play import PlayInstrumentation as BasePlayInstrumentation

logger = logging.getLogger(__name__)


class PlayInstrumentation(BasePlayInstrumentation):
    """Configure how a play should be instrumented."""

    def __init__(self) -> None:
        """Required because parent class is poorly implemented..."""
        pass

    def actor_started(self, play: Play, actor: Actor) -> None:
        """Observe actor started."""
        logger.info(
            f"Started actor '{actor.handler.__class__.__name__}' for events: {actor.source}"
        )

    def actor_cancelled(self, play: Play, actor: Actor) -> None:
        """Observe actor cancelled."""
        logger.warning(
            f"Cancelled actor '{actor.handler.__class__.__name__}' for events: {actor.source}"
        )

    def event_processing_failed(
        self,
        play: Play,
        actor: Actor,
        msg: BaseMessage[t.Any, t.Any, t.Any, t.Any],
        exc: BaseException,
    ) -> None:
        """Observe an exception raised by an actor."""
        logger.error(
            f"Actor '{actor.handler.__class__.__name__}' failed on subject {msg.subject} (event: {msg.spec}) with error: {exc}"
        )

    def event_processed(
        self,
        play: Play,
        actor: Actor,
        msg: BaseMessage[t.Any, t.Any, t.Any, t.Any],
    ) -> None:
        """Observe a successful command processed"""
        logger.info(
            f"Actor '{actor.handler.__class__.__name__}' processed a message on subject {msg.subject}"
        )

    def play_starting(self, play: "Play") -> None:
        """Observe play starting."""
        logger.info("Starting all actors")

    def play_started(self, play: "Play") -> None:
        """Observe play started."""
        logger.info("Started all actors")

    def play_stopping(self, play: "Play") -> None:
        """Observe play stopping."""
        logger.warning("Stopping all actors")

    def play_failed(self, play: "Play", errors: t.List[BaseException]) -> None:
        """Observe play failed."""
        logger.error(f"Stopped all actors due to errors: {errors}")

    def play_stopped(self, play: "Play") -> None:
        """Observe play stopped."""
        logger.warning("Stopped all actors")
