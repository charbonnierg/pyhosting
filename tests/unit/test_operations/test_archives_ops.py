from pathlib import Path
from re import escape
from tempfile import TemporaryDirectory

import pytest

from pyhosting.domain.errors import EmptyContentError, InvalidContentError
from pyhosting.domain.operations.archives import (
    create_archive,
    create_archive_from_content,
    unpack_archive,
    validate_filenames,
    validate_tarfile,
)

TEST_CONTENT = "test_content"
TEST_INDEX = "index.html"


@pytest.fixture
def root():
    """A temporary directory"""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def spa():
    """Path to test Single Page Application directory"""
    return Path(__file__).parent / "data" / TEST_CONTENT


@pytest.fixture
def single_file(spa: Path):
    return spa / TEST_INDEX


def check_spa_dir(path: Path):
    assert path.joinpath("index.html").is_file(), list(path.glob("*"))
    assert path.joinpath("some.css").is_file(), list(path.glob("*"))
    assert path.joinpath("some.js").is_file(), list(path.glob("*"))
    assert path.joinpath("static").is_dir(), list(path.glob("*"))
    assert path.joinpath("static/some.png").is_file(), list(path.glob("*"))


class TestArchivesOperations:
    def test_create_tarfile_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            create_archive("not-an-existing-directory")

    def test_validate_tarfile_empty_content(self):
        with pytest.raises(EmptyContentError, match="Content is empty"):
            validate_tarfile(b"")

    def test_unpack_tarfile_empty_content(self, root: Path):
        with pytest.raises(EmptyContentError, match="Content is empty"):
            unpack_archive(b"", root / "test")

    def test_validate_tarfile_invalid_content(self):
        with pytest.raises(
            InvalidContentError, match="Content is not a valid tar archive"
        ):
            validate_tarfile(b"invalid")
            validate_tarfile(b"invalid", 100000)

    def test_validate_filenames_missing_html(self):
        with pytest.raises(
            InvalidContentError,
            match=escape("No index.html found in content. Files found: []"),
        ):
            validate_filenames([])

    def test_validate_filenames_html_present_but_not_in_root_or_first_child_dir(self):
        with pytest.raises(
            InvalidContentError,
            match=escape(
                "No index.html found in content. Files found: ['test', 'test/subdir', 'test/subdir/index.html']"
            ),
        ):
            validate_filenames(["test", "test/subdir", "test/subdir/index.html"])

    def test_unpack_archive_invalid_content(self, root: Path):
        with pytest.raises(
            InvalidContentError, match="Content is not a valid tar archive"
        ):
            unpack_archive(b"invalid", root / "test")

    def test_create_archive_with_top_level_directory(self, root: Path, spa: Path):
        compressed = create_archive(spa, omit_top_level=False)
        assert validate_tarfile(compressed) == [
            "test_content",
            "test_content/index.html",
            "test_content/some.css",
            "test_content/some.js",
            "test_content/static",
            "test_content/static/some.png",
        ]
        destination = root.joinpath("test")
        unpack_archive(compressed, destination=destination, omit_top_level=False)
        assert destination.is_dir()
        check_spa_dir(destination / "test_content")

    def test_create_archive_without_top_level_directory(self, root: Path, spa: Path):
        compressed = create_archive(spa, omit_top_level=True)
        assert validate_tarfile(compressed) == [
            "./index.html",
            "./some.css",
            "./some.js",
            "./static",
            "./static/some.png",
        ]
        destination = root.joinpath("test")
        unpack_archive(compressed, destination=destination, omit_top_level=False)
        assert destination.is_dir()
        check_spa_dir(destination)

    def test_unpack_archive_with_top_level_directory(self, root: Path, spa: Path):
        compressed = create_archive(spa)
        destination = root.joinpath("test")
        unpack_archive(compressed, destination=destination, omit_top_level=False)
        assert destination.is_dir()
        check_spa_dir(destination / "test_content")

    def test_unpack_archive_without_top_level_directory(self, root: Path, spa: Path):
        compressed = create_archive(spa)
        destination = root.joinpath("test")
        unpack_archive(compressed, destination=destination, omit_top_level=True)
        assert destination.is_dir()
        check_spa_dir(destination)

    def test_create_archive_and_unpack_archive_with_top_level_idempotent(
        self, root: Path, spa: Path
    ):
        # Start by compression
        compressed = create_archive(spa)
        # Uncompress
        unpack_archive(compressed, destination=root / "test", omit_top_level=False)
        check_spa_dir(root / "test" / TEST_CONTENT)
        # Compress
        compressed_copy = create_archive(root / "test" / TEST_CONTENT)
        # Uncompress
        unpack_archive(compressed_copy, destination=root / "copy", omit_top_level=False)
        check_spa_dir(root / "copy" / TEST_CONTENT)

    def test_create_archive_and_unpack_archive_without_top_level_idempotent(
        self, root: Path, spa: Path
    ):
        # Start by compression
        compressed = create_archive(spa)
        # Uncompress
        unpack_archive(compressed, destination=root / "test", omit_top_level=True)
        check_spa_dir(root / "test")
        # Compress
        compressed_copy = create_archive(root / "test")
        # Uncompress
        unpack_archive(compressed_copy, destination=root / "copy", omit_top_level=True)
        check_spa_dir(root / "copy")

    def test_create_archive_from_single_file(self, root: Path, single_file: Path):
        compressed = create_archive(single_file)
        destination = root / "test"
        unpack_archive(compressed, root / "test")
        assert (
            destination.joinpath("index.html").read_bytes() == single_file.read_bytes()
        )

    def test_create_archive_from_single_file_without_top_level(
        self, root: Path, single_file: Path
    ):
        compressed = create_archive(single_file)
        destination = root / "test"
        unpack_archive(compressed, root / "test", omit_top_level=True)
        assert (
            destination.joinpath("index.html").read_bytes() == single_file.read_bytes()
        )

    def test_create_archive_from_content_empty(self):
        with pytest.raises(EmptyContentError):
            create_archive_from_content(b"")

    def test_create_archive_from_content_default(self, root: Path):
        archive = create_archive_from_content(b"<html></html>")
        destination = root / "test"
        unpack_archive(archive, destination=destination)
        assert destination.joinpath("index.html").read_bytes() == b"<html></html>"

    def test_create_archive_from_content_custom(self, root: Path):
        archive = create_archive_from_content(b"{}", filename="test.json")
        destination = root / "test"
        unpack_archive(archive, destination=destination)
        assert destination.joinpath("test.json").read_bytes() == b"{}"
