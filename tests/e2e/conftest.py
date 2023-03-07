import typing as t

import pytest
from genid import IDGenerator

from pyhosting.applications.controlplane.factory import create_app
from pyhosting.clients.controlplane.testing import HTTPTestClient
from pyhosting.domain.gateways import EventBusGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository


@pytest.fixture
def client(
    id_generator: IDGenerator,
    event_bus: EventBusGateway,
    page_repository: PageRepository,
    version_repository: PageVersionRepository,
    clock: t.Callable[[], int],
) -> t.Iterator[HTTPTestClient]:
    """Create an HTTP client to use within tests."""
    test_client = HTTPTestClient(
        create_app(
            id_generator,
            page_repository=page_repository,
            version_repository=version_repository,
            event_bus=event_bus,
            clock=clock,
        )
    )
    with test_client:
        yield test_client
