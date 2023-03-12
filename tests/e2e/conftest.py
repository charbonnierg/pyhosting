import typing as t

import pytest
from genid import IDGenerator

from pyhosting.adapters.clients.http.testing import PagesAPITestHTTPClient
from pyhosting.applications.controlplane.factory import create_app
from pyhosting.domain.repositories import PageRepository
from synopsys import EventBus


@pytest.fixture
def client(
    id_generator: IDGenerator,
    event_bus: EventBus,
    page_repository: PageRepository,
    clock: t.Callable[[], int],
) -> t.Iterator[PagesAPITestHTTPClient]:
    """Create an HTTP client to use within tests."""
    test_client = PagesAPITestHTTPClient(
        create_app(
            id_generator=id_generator,
            page_repository=page_repository,
            event_bus=event_bus,
            clock=clock,
        )
    )
    with test_client:
        yield test_client
