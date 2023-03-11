import typing as t
from logging import basicConfig

from starlette.applications import Starlette
from starlette.routing import Mount

from pyhosting.adapters.gateways.memory import InMemoryBlobStorage
from pyhosting.adapters.gateways.temporary import TemporaryDirectory
from pyhosting.domain import events
from pyhosting.domain.actors import sync_local
from pyhosting.domain.gateways import BlobStorageGateway, LocalStorageGateway
from synopsys import EventBus, Play, Subscriber
from synopsys.adapters.memory import InMemoryEventBus

from .controllers.http import (
    HealthCheckRouter,
    LatestFileserver,
    StaticFileServer,
    VersionFileServer,
)


def create_app(
    event_bus: t.Optional[EventBus] = None,
    storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[LocalStorageGateway] = None,
    base_url: str = "http://localhost:8000",
) -> Starlette:
    """Create  a new Data Plane starlette application.

    Assuming proper arguments are provided, application can be entirely deterministic.
    """
    basicConfig(level="DEBUG", format="%(levelname)s:     %(message)s")
    event_bus = event_bus or InMemoryEventBus()
    blob_storage = storage or InMemoryBlobStorage()
    local_storage = local_storage or TemporaryDirectory()
    actors = Play(
        bus=event_bus,
        actors=[
            Subscriber(
                event=events.PAGE_CREATED,
                handler=sync_local.GenerateDefaultIndexOnPageCreated(
                    local_storage=local_storage, base_url=base_url
                ),
            ),
            Subscriber(
                event=events.PAGE_DELETED,
                handler=sync_local.CleanLocalStorageOnPageDeleted(
                    local_storage=local_storage
                ),
            ),
            Subscriber(
                event=events.PAGE_VERSION_DELETED,
                handler=sync_local.CleanLocalStorageOnVersionDeleted(
                    local_storage=local_storage
                ),
            ),
            Subscriber(
                event=events.PAGE_VERSION_UPLOADED,
                handler=sync_local.DownloadToLocalStorageOnVersionUploaded(
                    local_storage=local_storage, blob_storage=blob_storage
                ),
            ),
        ],
    )
    app = Starlette(
        routes=[
            Mount("/static", StaticFileServer()),
            Mount("/versions", VersionFileServer(local_storage)),
            Mount("/health", HealthCheckRouter(actors)),
            Mount(
                "/",
                LatestFileserver(local_storage),
            ),
        ],
        lifespan=lambda _: actors,
    )
    return app
