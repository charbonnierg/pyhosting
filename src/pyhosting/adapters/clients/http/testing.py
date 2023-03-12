import typing as t

from starlette.applications import Starlette
from starlette.testclient import TestClient as _TestClient

from .pages import BasePagesAPIHTTPClient


class PagesAPITestHTTPClient(BasePagesAPIHTTPClient):
    """A test client which can be used to test PagesAPI HTTP controllers.

    It does not send requests accross the network, but still behave like a normal HTTP client.
    Instead of taking a base URL as argument, this client takes a Starlette (or FastAPI) application as argument.
    """

    def __init__(self, app: Starlette) -> None:
        """Create a new test client by providing an application instance.

        Note that application lifespan is not started unless test client is used
        as a context manager.
        """
        super().__init__(_TestClient(app))

    def __enter__(self) -> "PagesAPITestHTTPClient":
        """Test client must be entered as a context manager in order to start applications lifespan."""
        self.http.__enter__()
        return self

    def __exit__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Test client must be exited as a context manager in order to stop applications lifespan."""
        self.http.__exit__(*args, **kwargs)
