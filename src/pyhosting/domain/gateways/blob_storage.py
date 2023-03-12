import abc
import typing as t


class BlobStorageGateway(metaclass=abc.ABCMeta):
    """Interact with a remote blob storage."""

    @abc.abstractmethod
    async def put(self, *key: str, blob: bytes) -> None:
        """Put blob under given key.

        Arguments:
            key: key parts to put blob under. The key under which blob is stored is derived using `get_key` method.
            blob: the bytes to upload

        Returns:
            None
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def get(self, *key: str) -> bytes:
        """Read bytes under given key.

        Raises:
            BlobNotFoundError: When no blob exist for given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete(self, *key: str) -> None:
        """Delete bytes under given key.

        Raises:
            BlobNotFoundError: When no blob exist for given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_keys(self, *prefixes: str) -> t.List[str]:
        """List keys starting with prefix.

        Arguments:
            prefixes: when provided, keys starting with prefix derived using the `.get_key()` method are returned. When no prefix is provided, all blob keys found in storage are returned.

        Returns:
            A list of keys
        """
        raise NotImplementedError  # pragma: no cover
