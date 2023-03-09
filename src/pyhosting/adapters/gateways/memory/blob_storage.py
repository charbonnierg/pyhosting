import typing as t

from pyhosting.domain.gateways import BlobStorageGateway

T = t.TypeVar("T")


class InMemoryBlobStorage(BlobStorageGateway):
    def __init__(self) -> None:
        self._store: t.Dict[str, bytes] = {}

    async def get_version(self, page_id: str, page_version: str) -> t.Optional[bytes]:
        key = "/".join([page_id, page_version])
        return self._store.get(key, None)

    async def put_version(
        self, page_id: str, page_version: str, content: bytes
    ) -> None:
        key = "/".join([page_id, page_version])
        self._store[key] = content

    async def delete_version(self, page_id: str, page_version: str) -> bool:
        key = "/".join([page_id, page_version])
        return self._store.pop(key, None) is not None

    async def list_versions(self, page_id: str) -> t.List[str]:
        return [key for key in self._store if key.startswith(page_id)]
