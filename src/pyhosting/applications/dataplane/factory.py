import typing as t

from starlette.applications import Starlette
from starlette.routing import Mount

from pyhosting.domain import events
from pyhosting.domain.gateways import (
    BlobStorageGateway,
    FilestorageGateway,
    TemplateLoader,
)
from pyhosting.domain.usecases.effects import pages_data_plane
from synopsys import EventBus, Play, Subscriber

from .defaults import defaults
from .routes.http import (
    HealthCheckRouter,
    LatestFileserver,
    StaticFileServer,
    VersionFileServer,
)


def create_app(
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[FilestorageGateway] = None,
    templates: t.Optional[TemplateLoader] = None,
    base_url: str = "http://localhost:8000",
) -> Starlette:
    """Create  a new Data Plane starlette application.

    Assuming proper arguments are provided, application can be entirely deterministic.
    """
    event_bus, blob_storage, local_storage, templates = defaults(
        event_bus,
        blob_storage,
        local_storage,
        templates,
    )

    actors = Play(
        bus=event_bus,
        actors=[
            Subscriber(
                event=events.PAGE_CREATED,
                handler=pages_data_plane.InitCacheOnPageCreated(
                    local_storage=local_storage,
                    base_url=base_url,
                    templates=templates,
                ),
            ),
            Subscriber(
                event=events.PAGE_DELETED,
                handler=pages_data_plane.CleanCacheOnPageDeleted(
                    local_storage=local_storage
                ),
            ),
            Subscriber(
                event=events.VERSION_DELETED,
                handler=pages_data_plane.CleanCacheOnVersionDeleted(
                    local_storage=local_storage
                ),
            ),
            Subscriber(
                event=events.VERSION_UPLOADED,
                handler=pages_data_plane.UpdateCacheOnVersionUploaded(
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
