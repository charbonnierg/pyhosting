import os
from pathlib import Path

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from pyhosting.domain.gateways import FilestorageGateway

STATIC_ROOT = Path(__file__).parent.joinpath("static")


class LatestFileserver(StaticFiles):
    """File server used to serve requests for latest pages versions."""

    def __init__(
        self,
        storage: FilestorageGateway,
    ) -> None:
        self.storage = storage
        super().__init__(
            directory=storage.root,
            packages=None,
            html=True,
            check_dir=True,
            follow_symlink=True,
        )

    def get_path(self, scope: Scope) -> str:
        """Get path to file for a latest page request.

        LocalStorage stores page versions indexed by version.
        latest version when it exist is a symlink to an existing version
        Receive: `/something/`
        Transforms: `/something/versions/latest`
        Symlink to: `/something/versions/XXX`
        """
        path: str = os.path.normpath(os.path.join(*scope["path"].split("/")))
        page_name, *rest = path.split("/")
        target = self.storage.get_path(page_name, "__latest__")
        if target.exists():
            return target.joinpath(*rest).as_posix()
        default_target = self.storage.get_path(page_name, "__default__")
        return default_target.as_posix()


class VersionFileServer(StaticFiles):
    """File server used to serve requests for specific pages versions."""

    def __init__(
        self,
        storage: FilestorageGateway,
    ) -> None:
        self.storage = storage
        super().__init__(
            directory=storage.root,
            packages=None,
            html=True,
            check_dir=True,
            follow_symlink=False,
        )


class StaticFileServer(StaticFiles):
    """File server used to serve static files (css, js)"""

    def __init__(
        self,
    ) -> None:
        super().__init__(
            directory=STATIC_ROOT,
            packages=None,
            html=False,
            check_dir=True,
            follow_symlink=False,
        )
