import os
from pathlib import Path

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from pyhosting.domain.gateways import LocalStorageGateway

STATIC_ROOT = Path(__file__).parent.joinpath("static")


class LatestFileserver(StaticFiles):
    """File server used to serve requests for latest pages versions."""

    def __init__(
        self,
        storage: LocalStorageGateway,
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
        return self.storage.get_latest_path_or_default(
            page_name=page_name, remaining=rest
        )


class VersionFileServer(StaticFiles):
    """File server used to serve requests for specific pages versions."""

    def __init__(
        self,
        storage: LocalStorageGateway,
    ) -> None:
        self.storage = storage
        super().__init__(
            directory=storage.root,
            packages=None,
            html=True,
            check_dir=True,
            follow_symlink=False,
        )

    def get_path(self, scope: Scope) -> str:
        """Get path to file for a page version request.

        LocalStorage stores page versions indexed by version.
        Receive: `/something/1`
        Transforms: `/something/versions/1`
        """
        path: str = os.path.normpath(os.path.join(*scope["path"].split("/")))
        page_name, version, *rest = path.split("/")
        return self.storage.get_version_path(
            page_name=page_name, version=version, remaining=rest
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
