"""A module to interact with `.tar.gz` or `.tar` archives of static web applications.

It exposes methods to:
- create in-memory `tar` archives from directories
- create in-memory `tar` archives from bytes
- decompress in-memory `tar` archives from bytes into directories

This module does NOT expose a method to decompress a `tar` archive present on filesytem,
as it is not required by the applications.
"""
import io
import tarfile
import typing as t
from pathlib import Path
from tarfile import is_tarfile as is_tarfile  # noqa: F401
from tempfile import TemporaryDirectory

from ..errors import EmptyContentError, InvalidContentError


def _members_without_top_level(tar: tarfile.TarFile) -> t.Iterator[tarfile.TarInfo]:
    """Return members of a tar archive stripped from the top level directory."""
    for member in tar.getmembers():
        member.path = member.path.split("/", 1)[-1]
        yield member


def _members_with_top_level(tar: tarfile.TarFile) -> t.Iterator[tarfile.TarInfo]:
    """Return members of a tar archive with top level directory."""
    for member in tar.getmembers():
        if member.path == ".":
            continue
        yield member


def _members(
    tar: tarfile.TarFile, omit_top_level: bool = False
) -> t.Iterator[tarfile.TarInfo]:
    if omit_top_level:
        return _members_without_top_level(tar)
    return _members_with_top_level(tar)


def unpack_archive(
    content: bytes,
    destination: t.Union[str, Path],
    omit_top_level: bool = False,
    create_parents: bool = False,
) -> Path:
    """Extract some tar archive into given destination directory.

    Arguments:
        content: the tar file to decompress as bytes
        destination: the path to the directory where archive should be unpacked
        omit_top_level: when false (the default) destination will contain a single parent directory with the same name as `source`.
            when true, destination will contain files found in `source` directory without a parent directory.
        create_parents: when false (the default) an error is raised if destination parent directory does not exist.
            When true, destination parent directories are created if needed.
    """
    if not content:
        raise EmptyContentError()
    # Load tar archive into BytesIO
    tar_io = io.BytesIO(content)
    # Initialize destination path
    destination = Path(destination)
    # Create parent directory when required
    if create_parents:
        destination.parent.mkdir(parents=True, exist_ok=True)
    # Try to open the tar file
    try:
        tar = tarfile.open(fileobj=tar_io)
    except tarfile.TarError as exc:
        raise InvalidContentError("Content is not a valid tar archive") from exc
    # Try to extract tar file
    try:
        tar.extractall(
            path=destination,
            members=_members(tar, omit_top_level=omit_top_level),
        )
    # Always close tarfile
    finally:
        tar.close()
    # Return destination
    return destination


def create_archive(
    source: t.Union[str, Path],
    compression: str = "gz",
    omit_top_level: bool = False,
) -> bytes:
    """Create an in-memory compressed archive from a file or a directory.

    Arguments:
        source: the path to a file or a directory to archive
        compression: the compression algorithm
        omit_top_level: when false (the default) archive will contain a single parent directory with the same name as `source`.
            when true, archive will contain files found in `source` directory without parent directory.

    Returns:
        A tar archive as bytes
    """
    tar_io = io.BytesIO()
    source = Path(source).expanduser().resolve(True)
    with tarfile.open(fileobj=tar_io, mode=f"w:{compression}") as tar:
        tar.add(source, arcname="." if omit_top_level else source.name, recursive=True)
    tar_io.seek(0)
    return tar_io.read()


def validate_tarfile(content: bytes, block_size: int = 1024) -> t.List[str]:
    """Iterate over all members of an archive to validate that archive is a valid tar archive.

    Raises:
        InvalidContentError: When archive is not a tarfile
    """
    if not content:
        raise EmptyContentError()
    tar_io = io.BytesIO(content)
    members: t.List[str] = []
    try:
        with tarfile.open(fileobj=tar_io) as tar:
            for member in tar.getmembers():
                if member.name != ".":
                    members.append(member.name)
                reader_context = tar.extractfile(member.name)
                if reader_context is None:
                    continue
                with reader_context as reader:
                    for _ in iter(lambda: reader.read(block_size), b""):
                        # Simply continue to validate each file integrity
                        continue
    except tarfile.TarError as exc:
        raise InvalidContentError("Content is not a valid tar archive") from exc
    return members


def validate_filenames(filenames: t.List[str], expect_file: str = "index.html") -> None:
    """Validate that a file named index.html is present within a list of filenames.

    File can either be at the top level or in a child directory of the top level directory.

    Raises:
        InvalidContentError: When archive is not a tarfile or index.html is not found
    """
    # Check that an index.html file is present
    if expect_file not in filenames:
        index_found = False
        for filename in filenames:
            try:
                _, filename = filename.split("/", maxsplit=1)
            except ValueError:
                continue
            if filename == expect_file:
                index_found = True
                break
        if not index_found:
            raise InvalidContentError(
                f"No index.html found in content. Files found: {filenames}"
            )


def validate_archive(
    content: bytes, block_size: int = 1024, expect_file: str = "index.html"
) -> t.List[str]:
    """Validate that some bytes are a valid tar archive with an index.html file.

    Raises:
        EmptyContentError: When content is empty
        InvalidContentError: When archive is not a tarfile or index.html is not found
    """
    filenames = validate_tarfile(content, block_size=block_size)
    validate_filenames(filenames, expect_file=expect_file)
    return filenames


def create_archive_from_content(content: bytes, filename: str = "index.html") -> bytes:
    """This function is mainly useful within tests.

    It can be used to create a valid tar archive holding a single file named according
    to `filename` argument. Archive is returned as bytes.

    Arguments:
        content: the content to write into archive file.
        filename: the name of the file to create within the archive.

    Returns:
        A tar archive as bytes
    """
    if not content:
        raise EmptyContentError()
    with TemporaryDirectory() as tmpdir:
        source = Path(tmpdir).joinpath(filename)
        source.write_bytes(content)
        return create_archive(source)
