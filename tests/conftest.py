import typing as t
from time import time

import pytest
from _pytest.fixtures import SubRequest
from genid import IDGenerator, generator

from pyhosting.adapters.gateways.memory import InMemoryBlobStorage
from pyhosting.adapters.gateways.temporary import TemporaryDirectory
from pyhosting.adapters.repositories.memory import (
    InMemoryPageRepository,
    InMemoryPageVersionRepository,
)
from pyhosting.core import EventBus
from pyhosting.core.adapters.memory import InMemoryEventBus
from pyhosting.domain.gateways import BlobStorageGateway, LocalStorageGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository


@pytest.fixture
def clock(request: SubRequest) -> t.Callable[[], int]:
    return getattr(request, "param", lambda: int(time()))


@pytest.fixture
def id_generator(request: SubRequest) -> IDGenerator:
    param = getattr(request, "param", "incremental")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    return generator(kind, **options)


@pytest.fixture
def event_bus(request: SubRequest) -> EventBus:
    """Create an event bus to use within tests."""
    param = getattr(request, "param", "memory")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    if kind == "memory":
        return InMemoryEventBus(**options)
    raise ValueError(f"Unknown event bus implementation: {kind}")


@pytest.fixture
def page_repository(request: SubRequest) -> PageRepository:
    """Create a page repository to use within tests."""
    param = getattr(request, "param", "memory")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    if kind == "memory":
        return InMemoryPageRepository(**options)
    raise ValueError(f"Unknown page repository implementation: {kind}")


@pytest.fixture
def version_repository(request: SubRequest) -> PageVersionRepository:
    """Create a page version repository to use within tests."""
    param = getattr(request, "param", "memory")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    if kind == "memory":
        return InMemoryPageVersionRepository(**options)
    raise ValueError(f"Unknown page version repository implementation: {kind}")


@pytest.fixture
def blob_storage(request: SubRequest) -> BlobStorageGateway:
    """Create a blob storage to use within tests."""
    param = getattr(request, "param", "memory")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    if kind == "memory":
        return InMemoryBlobStorage(**options)
    raise ValueError(f"Unknown blob storage implementation: {kind}")


@pytest.fixture
def local_storage(request: SubRequest) -> LocalStorageGateway:
    """Create a local storage to use within tests."""
    param = getattr(request, "param", "temporary")
    if isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    if kind == "temporary":
        return TemporaryDirectory(**options)
    raise ValueError(f"Unknown local storage implementation: {kind}")
