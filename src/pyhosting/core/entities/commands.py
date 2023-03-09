import typing as t

CommandT = t.TypeVar("CommandT")
ReplyT = t.TypeVar("ReplyT")


class Command(t.Generic[CommandT, ReplyT]):
    """A command is an association of a subject, a request schema, and a reply schema"""

    name: str
    """The command name."""

    schema: t.Type[CommandT]
    """The request schema."""

    reply_schema: t.Type[ReplyT]
    """The reply schema."""

    timeout: t.Optional[float]
    """The timeout used when sending the command.

    When set to None, command does not use a timeout.
    """

    @property
    def subject(self) -> str:
        """Return subject"""
        return self.name

    def __init__(
        self,
        name: str,
        schema: t.Type[CommandT],
        reply_schema: t.Type[ReplyT],
        timeout: t.Optional[float] = None,
    ) -> None:
        """Create a new command."""
        self.name = name
        self.schema = schema
        self.reply_schema = reply_schema
        self.timeout = timeout
