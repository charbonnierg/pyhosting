import asyncio
import typing as t

from ..core.interfaces import Message

MsgT = t.TypeVar("MsgT", bound=Message[t.Any, t.Any, t.Any])


class Waiter(t.Generic[MsgT]):
    def __init__(
        self,
        observable: t.AsyncContextManager[t.AsyncIterator[MsgT]],
    ) -> None:
        """Do not use __init__ constructor directly. Instead of .create() classmethod."""
        self.channel = observable
        self.task = asyncio.create_task(self.__start_in_foreground())

    async def __start_in_foreground(self) -> MsgT:
        """Wait for a single event."""
        async with self.channel as observer:
            async for item in observer:
                return item
        raise ValueError("No event received")

    @classmethod
    async def create(
        cls,
        channel: t.AsyncContextManager[t.AsyncIterator[MsgT]],
    ) -> "Waiter[MsgT]":
        """Create and start waiter in background."""
        waiter = cls(channel)
        await asyncio.sleep(0)
        return waiter

    async def wait(self, timeout: t.Optional[float] = 5) -> MsgT:
        """Wait until event is received"""
        return await asyncio.wait_for(self.task, timeout=timeout)
