import typing as t

from pydantic import parse_obj_as, parse_raw_as

from synopsys.core.interfaces import Codec

from .json import dump

T = t.TypeVar("T")


class PydanticCodec(Codec):
    def encode(self, data: t.Any) -> bytes:
        return dump(data)

    def decode(self, raw: bytes, schema: t.Type[T]) -> T:
        if schema is bytes and isinstance(raw, bytes):
            return t.cast(T, raw)
        return parse_raw_as(schema, raw)

    def parse_obj(
        self,
        data: t.Any,
        schema: t.Type[T],
    ) -> T:
        return parse_obj_as(schema, data)
