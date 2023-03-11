import typing as t

from starlette.applications import Starlette
from starlette.testclient import TestClient as _TestClient

from .http import BaseHTTPPagesClient


class InMemoryHTTPPagesClient(BaseHTTPPagesClient):
    """An HTTP client which can be used to test a starlette or a fastapi application.

    It does not send requests accross the network, but still behave like a normal HTTP client.

    Instead of taking a base URL as argument, this client takes a Starlette (or FastAPI) application as argument.
    """

    def __init__(self, app: Starlette) -> None:
        super().__init__(_TestClient(app))

    def __enter__(self) -> "InMemoryHTTPPagesClient":
        self.http.__enter__()
        return self

    def __exit__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self.http.__exit__(*args, **kwargs)
