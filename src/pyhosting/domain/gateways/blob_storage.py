import abc
import typing as t


class BlobStorageGateway(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def put_version(
        self, page_id: str, page_version: str, content: bytes
    ) -> None:
        """Put some content under given key."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def get_version(self, page_id: str, page_version: str) -> t.Optional[bytes]:
        """Get some content under given key."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete_version(self, page_id: str, page_version: str) -> bool:
        """Delete some content under given key."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_versions(self, page_id: str) -> t.List[str]:
        """List versions for a page"""
        raise NotImplementedError  # pragma: no cover
