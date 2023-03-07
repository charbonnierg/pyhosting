import abc
import typing as t
from pathlib import Path


class LocalStorageGateway(metaclass=abc.ABCMeta):
    @abc.abstractproperty
    def root(self) -> Path:
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_version_path(
        self,
        page_name: str,
        version: str,
        remaining: t.Optional[t.Iterable[str]] = None,
    ) -> str:
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_latest_path_or_default(
        self, page_name: str, remaining: t.Optional[t.Iterable[str]] = None
    ) -> str:
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def unpack_archive(
        self, page_name: str, version: str, content: bytes, latest: bool
    ) -> None:
        """Unpack some bytes under given directory."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def write_default_file(self, page_name: str, content: bytes) -> None:
        """Write a file into given directory"""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def remove_directory(
        self, page_name: str, version: t.Optional[str] = None
    ) -> bool:
        """Remove some directory."""
        raise NotImplementedError  # pragma: no cover
