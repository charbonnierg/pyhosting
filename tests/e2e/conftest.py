import typing as t

import pytest
from genid import IDGenerator

from pyhosting.applications.controlplane.factory import create_app
from pyhosting.adapters.clients.pages.testing import InMemoryHTTPPagesClient
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from synopsys import EventBus


@pytest.fixture
def client(
    id_generator: IDGenerator,
    event_bus: EventBus,
    page_repository: PageRepository,
    version_repository: PageVersionRepository,
    clock: t.Callable[[], int],
) -> t.Iterator[InMemoryHTTPPagesClient]:
    """Create an HTTP client to use within tests."""
    test_client = InMemoryHTTPPagesClient(
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
