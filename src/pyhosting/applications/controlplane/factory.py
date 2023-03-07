import typing as t
from time import time

from genid import IDGenerator, ObjectIDGenerator
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from pyhosting.applications.dataplane.factory import create_app as create_agent_app
from pyhosting.domain.actors import sync_blob, sync_local
from pyhosting.domain.gateways import (
    BlobStorageGateway,
    EventBusGateway,
    LocalStorageGateway,
)
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from pyhosting.infrastructure.actors.asyncio import AsyncioActors
from pyhosting.infrastructure.gateways.local import TemporaryDirectory
from pyhosting.infrastructure.gateways.memory import (
    InMemoryBlobStorage,
    InMemoryEventBus,
)
from pyhosting.infrastructure.repositories.memory import (
    InMemoryPageRepository,
    InMemoryPageVersionRepository,
)

from .controllers.http.pages import PagesAPIRouter
from .controllers.http.version import get_version


def create_app(
    id_generator: t.Optional[IDGenerator] = None,
    page_repository: t.Optional[PageRepository] = None,
    version_repository: t.Optional[PageVersionRepository] = None,
    event_bus: t.Optional[EventBusGateway] = None,
    storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[LocalStorageGateway] = None,
    clock: t.Callable[[], int] = lambda: int(time()),
    base_url: str = "http://localhost:8000",
) -> Starlette:
    """Create  a new Control Plane starlette application.

    Assuming proper arguments are provided, application can be entirely deterministic.
    """
    id_generator = id_generator or ObjectIDGenerator()
    page_repository = page_repository or InMemoryPageRepository()
    version_repository = version_repository or InMemoryPageVersionRepository()
    event_bus = event_bus or InMemoryEventBus()
    blob_storage = storage or InMemoryBlobStorage()
    local_storage = local_storage or TemporaryDirectory()
    actors = AsyncioActors(
        [
            sync_blob.CleanBlobStorageOnPageDelete(storage=blob_storage),
            sync_blob.UploadToBlobStorageOnVersionCreated(
                event_bus=event_bus, storage=blob_storage
            ),
            sync_blob.CleanBlobStorageOnVersionDelete(storage=blob_storage),
        ],
        event_bus=event_bus,
    )
    # Need to extend actors because starlette does not start lifespan of mounted apps
    actors.extend(
        [
            sync_local.GenerateDefaultIndexOnPageCreated(
                local_storage=local_storage, base_url=base_url
            ),
            sync_local.CleanLocalStorageOnPageDeleted(local_storage=local_storage),
            sync_local.CleanLocalStorageOnVersionDeleted(local_storage=local_storage),
            sync_local.DownloadToLocalStorageOnVersionUploaded(
                local_storage=local_storage, blob_storage=blob_storage
            ),
        ]
    )
    # Create starlette app (ASGI)
    app = Starlette(
        routes=[
            # API Version
            Route(
                "/api/version",
                get_version,
                methods=["GET"],
                name="get_version",
                include_in_schema=True,
            ),
            # Pages Api
            Mount(
                "/api/pages/",
                PagesAPIRouter(
                    id_generator=id_generator,
                    versions_repository=version_repository,
                    pages_repository=page_repository,
                    event_bus=event_bus,
                    clock=clock,
                ),
            ),
            # Mount fileserver
            Mount(
                "/pages/",
                create_agent_app(
                    event_bus=event_bus,
                    storage=blob_storage,
                    local_storage=local_storage,
                    base_url=base_url,
                ),
            ),
        ],
        lifespan=actors.lifespan,
    )
    return app
