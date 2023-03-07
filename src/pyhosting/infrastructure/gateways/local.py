import tarfile
import typing as t
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from weakref import finalize

from ...domain.gateways import LocalStorageGateway


class TemporaryDirectory(LocalStorageGateway):
    def __init__(self) -> None:
        self._dir = Path(mkdtemp())
        self._finalizer = finalize(self, self._clean)

    def _clean(self) -> None:
        rmtree(self._dir, ignore_errors=True)

    @property
    def root(self) -> Path:
        return self._dir

    def get_version_path(
        self,
        page_name: str,
        version: str,
        remaining: t.Optional[t.Iterable[str]] = None,
    ) -> str:
        target = self._dir / page_name / "versions" / version
        if remaining:
            return target.joinpath(*remaining).as_posix()
        return target.as_posix()

    def get_latest_path_or_default(
        self, page_name: str, remaining: t.Optional[t.Iterable[str]] = None
    ) -> str:
        target = self._dir / page_name / "versions/latest"
        if target.exists():
            if remaining:
                return target.joinpath(*remaining).as_posix()
            return target.as_posix()
        default_target = self._dir / page_name / "__default__"
        return default_target.as_posix()

    async def unpack_archive(
        self, page_name: str, version: str, content: bytes, latest: bool
    ) -> None:
        target = Path(self.get_version_path(page_name, version))
        target.mkdir(exist_ok=True, parents=True)
        archive = target.joinpath("archive")
        index = target.joinpath("index.html")
        archive.write_bytes(content)
        # Handle tar files
        if tarfile.is_tarfile(archive):
            with tarfile.open(archive) as tar:
                tar.extractall(target, members=_members(tar, 1))
            archive.unlink()
        # Consider everything else to be HTML files
        else:
            archive.rename(index)
        # Update latest symlink
        if latest:
            target.parent.joinpath("latest").unlink(missing_ok=True)
            target.parent.joinpath("latest").symlink_to(
                target, target_is_directory=True
            )

    async def write_default_file(self, page_name: str, content: bytes) -> None:
        target = self.root.joinpath(page_name) / "__default__" / "index.html"
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_bytes(content)

    async def remove_directory(
        self, page_name: str, version: t.Optional[str] = None
    ) -> bool:
        target = self._dir.joinpath(page_name)
        if version:
            target = target / "versions" / version
        exists = target.is_dir()
        rmtree(target, ignore_errors=True)
        return exists


def _members(tar: tarfile.TarFile, strip: int = 1) -> t.Iterator[tarfile.TarInfo]:
    for member in tar.getmembers():
        member.path = member.path.split("/", strip)[-1]
        yield member
