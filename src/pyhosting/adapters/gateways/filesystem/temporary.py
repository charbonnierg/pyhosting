from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from weakref import finalize

from .local import LocalDirectory


class TemporaryDirectory(LocalDirectory):
    """Temporary directories can be used during tests."""

    def __init__(self) -> None:
        temporary_directory = Path(mkdtemp())
        super().__init__(temporary_directory)
        self._finalizer = finalize(self, self._clean)

    def _clean(self) -> None:
        rmtree(self.root, ignore_errors=True)
