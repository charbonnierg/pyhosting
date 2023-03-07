import typing as t

from starlette.applications import Starlette
from starlette.testclient import TestClient as _TestClient

from .http import BaseHTTPControlPlaneClient


class HTTPTestClient(BaseHTTPControlPlaneClient):
    def __init__(self, app: Starlette) -> None:
        super().__init__(_TestClient(app))

    def __enter__(self) -> "HTTPTestClient":
        self.http.__enter__()
        return self

    def __exit__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.http.__exit__(*args, **kwargs)
