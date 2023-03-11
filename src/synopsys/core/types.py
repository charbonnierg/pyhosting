import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    EMPTY: t.Type[None] = type(None)
else:
    EMPTY = type(None)

DataT = t.TypeVar("DataT")
MetadataT = t.TypeVar("MetadataT")
ScopeT = t.TypeVar("ScopeT")
ReplyT = t.TypeVar("ReplyT")
