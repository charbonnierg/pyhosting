from pathlib import Path
from tempfile import TemporaryDirectory as _TemporaryDirectory

import pytest
from _pytest.fixtures import SubRequest

from pyhosting.adapters.gateways.filesystem import LocalDirectory, TemporaryDirectory
from pyhosting.domain.gateways import FilestorageGateway


@pytest.fixture
def directory(request: SubRequest):
    param = request.param
    if param == LocalDirectory:
        with _TemporaryDirectory() as tmpdir:
            yield LocalDirectory(tmpdir)
    else:
        yield param()


@pytest.mark.parametrize(
    "directory", [LocalDirectory, TemporaryDirectory], indirect=True
)
class TestLocalDirectoryAdapter:
    def test_root_property(self, directory: FilestorageGateway):
        """A FilesDirectory must have a root Path property"""
        assert isinstance(directory.root, Path)
        assert directory.root.is_dir()

    def test_get_path(self, directory: FilestorageGateway):
        assert directory.get_path("test") == directory.root.joinpath("test")
        assert directory.get_path("/test") == directory.root.joinpath("test")
        assert directory.get_path("//test") == directory.root.joinpath("test")
        assert directory.get_path("test/") == directory.root.joinpath("test")
        assert directory.get_path("test//") == directory.root.joinpath("test")
        assert directory.get_path("test", "1") == directory.root.joinpath("test/1")
        assert directory.get_path("test", "/1", "/3") == directory.root.joinpath(
            "test/1/3"
        )

    @pytest.mark.asyncio
    async def test_write_bytes(self, directory: FilestorageGateway):
        await directory.write_bytes("test", content=b"...")
        assert directory.get_path("test").read_bytes() == b"..."

        await directory.write_bytes("/test2", content=b"...")
        assert directory.root.joinpath("test2").read_bytes() == b"..."

    @pytest.mark.asyncio
    async def test_remove_directory(self, directory: FilestorageGateway):
        await directory.write_bytes("test/file", content=b"...", create_parents=True)
        await directory.remove_directory("test")
        assert not directory.get_path("test/file").exists()
        assert not directory.get_path("test").exists()


def test_temporary_directory_cleanup():
    directory = TemporaryDirectory()
    root = directory.root
    assert root.exists()
    directory._finalizer()
    assert not root.exists()
