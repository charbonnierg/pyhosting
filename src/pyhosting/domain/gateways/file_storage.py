import abc
from pathlib import Path


class FilestorageGateway(metaclass=abc.ABCMeta):
    """Interact with a files directory.

    Implementations should take care so that methods with side-effects
    (for example `write_bytes` or `remove_directory`) CANNOT modify filesystem
    outside of the directory.
    """

    @abc.abstractproperty
    def root(self) -> Path:
        """Get a path to file storage root directory."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def get_path(self, *parts: str) -> Path:
        """Get a path from relative path parts.

        This method does NOT check that path exist and MUST NOT
        raise an error when path does not exist.

        Also note that this method NEVER returns a path which is
        not a child path of the files directory root.

        As such, even if absolute file paths are provided,
        they are stripped from their leading slashes and are
        considered are relative paths.

        Arguments:
            parts: parts of filepath to get relative path for

        Returns:
            A path object
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def write_bytes(
        self,
        *destination: str,
        content: bytes,
        create_parents: bool = False,
    ) -> Path:
        """Write bytes to destination and return destination file path.

        Argument:
            destination: path or path parts where to write bytes
            content: bytes to write
            create_parents: when false (the default) an error is raised if destination parent directory does not exist. When true, parents directories are created when needed.

        Returns:
            A path object where bytes were written

        Raises:
            FileNotFoundError: when create_parents if False (the default) and destination parent directory does not exist.
            OSError: Various errors which can happen due to permissions
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def remove_directory(self, *path: str) -> bool:
        """Remove some directory.

        This method does NOT raise an error if directory does not exist.
        Instead it returns a boolean value indicating whether directory
        was deleted or did not exist in the first place.

        Arguments:
            path: one or several relative path parts pointing to directory to remove

        Returns:
            True when directory existed and was deleted, else False

        Raises:
            OSError: Various errors which can happen due to permissions
        """
        raise NotImplementedError  # pragma: no cover
