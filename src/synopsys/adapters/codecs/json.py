"""Module responsible for JSON serialization and deserialization.

The library orjson is used when available, else the standard library is used.
"""
import json
import typing as t
from dataclasses import asdict, is_dataclass
from datetime import datetime

from pydantic import BaseModel


def _default_serializer(obj: t.Any) -> t.Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (bytes, bytearray, set)):
        return list(obj)
    if isinstance(obj, BaseModel):
        return obj.dict()
    raise TypeError


def dumps(
    v: t.Any,
    *,
    default: t.Optional[t.Callable[..., t.Any]] = _default_serializer,
    indent: bool = False,
    sort_keys: bool = False,
    **kwargs: t.Any,
) -> str:
    """Serialize Python objects to a JSON string using standard library."""
    if v is None:
        return ""
    if v == b"":
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, datetime):
        return v.isoformat()
    if is_dataclass(v):
        v = asdict(v)
    if isinstance(v, BaseModel):
        return v.json(indent=indent if indent else 0, sort_keys=sort_keys)
    json_str = json.dumps(
        v,
        default=default,
        indent=2 if indent else 0,
        sort_keys=sort_keys,
        **kwargs,
    )
    if not indent:
        return json_str.replace("\n", "")
    return json_str


def dump(
    v: t.Any,
    *,
    default: t.Optional[t.Callable[..., t.Any]] = _default_serializer,
    indent: bool = False,
    sort_keys: bool = False,
    **kwargs: t.Any,
) -> bytes:
    """Serialize Python objects to JSON bytes using standard library."""
    if v is None:
        return b""
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        return v.encode("utf-8")
    if isinstance(v, BaseModel):
        return v.json(indent=indent if indent else 0, sort_keys=sort_keys).encode(
            "utf-8"
        )
    if isinstance(v, datetime):
        return v.isoformat().encode("utf-8")
    if is_dataclass(v):
        v = asdict(v)
    if isinstance(v, BaseModel):
        return v.json(indent=indent if indent else 0, sort_keys=sort_keys).encode(
            "utf-8"
        )
    return json.dumps(
        v,
        default=default,
        indent=indent,
        sort_keys=sort_keys,
        **kwargs,
    ).encode("utf-8")


__all__ = ["dump"]
