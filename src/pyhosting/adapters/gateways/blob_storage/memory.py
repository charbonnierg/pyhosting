import typing as t

from pyhosting.domain.errors import BlobNotFoundError
from pyhosting.domain.gateways import BlobStorageGateway

T = t.TypeVar("T")


class InMemoryBlobStorage(BlobStorageGateway):
    """An in-memory blob storage can be used during unit test to avoid writing mocks."""

    def __init__(self) -> None:
        """Create a new in-memory blob storage.

        Does not accept argument.
        """
        self._store: t.Dict[str, bytes] = {}

    def get_key(self, *parts: str) -> str:
        """Get a key from key parts"

        Arguments:
            parts: one or several key parts

        Returns:
            A single key derived from the key parts.
        """
        return "/".join(key.rstrip("/") for key in parts).lstrip("/")

    def split_key(self, key: str) -> t.List[str]:
        """Split a key into key parts.

        This method is the inverse of the `.get_key()` transformation.

        Arguments:
            key: a blob key as a string

        Returns:
            A list of key parts derived from key
        """
        return key.split("/")

    async def put(self, *key: str, blob: bytes) -> None:
        """Put blob under given key.

        Arguments:
            key: key parts to put blob under. The key under which blob is stored is derived using `get_key` method.
            blob: the bytes to upload

        Returns:
            None
        """
        derived_key = self.get_key(*key)
        self._store[derived_key] = blob

    async def get(self, *key: str) -> bytes:
        """Read blob under given key.

        Arguments:
            key: key parts used to derive key to get blob for

        Raises:
            BlobNotFoundError: When no blob exist for given key.
        """
        derived_key = self.get_key(*key)
        if derived_key not in self._store:
            raise BlobNotFoundError(derived_key)
        return self._store[derived_key]

    async def delete(self, *key: str) -> None:
        """Delete blob under given key.

        Arguments:
            key: key parts used to derive key to get blob for

        Raises:
            BlobNotFoundError: When no blob exist for given key.
        """
        derived_key = self.get_key(*key)
        if self._store.pop(derived_key, None) is None:
            raise BlobNotFoundError(derived_key)

    async def list_keys(self, *prefixes: str) -> t.List[str]:
        """List keys starting with prefix.

        Arguments:
            prefixes: when provided, keys starting with prefix derived using the `.get_key()` method are returned. When no prefix is provided, all blob keys found in storage are returned.

        Returns:
            A list of keys
        """
        if prefixes:
            prefix = self.get_key(*prefixes)
            return [key for key in self._store if key.startswith(prefix)]
        return list(self._store)
