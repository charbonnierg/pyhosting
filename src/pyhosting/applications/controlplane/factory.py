import typing as t
from time import time

from fastapi import FastAPI
from fastapi.routing import APIRoute
from genid import IDGenerator, ObjectIDGenerator
from starlette.routing import Mount

from pyhosting.adapters.gateways.memory import InMemoryBlobStorage
from pyhosting.adapters.gateways.temporary import TemporaryDirectory
from pyhosting.adapters.repositories.memory import (
    InMemoryPageRepository,
    InMemoryPageVersionRepository,
)
from pyhosting.applications.dataplane.factory import create_app as create_agent_app
from pyhosting.domain import events
from pyhosting.domain.actors import sync_blob, sync_local
from pyhosting.domain.gateways import BlobStorageGateway, LocalStorageGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from synopsys import EventBus, Play, Subscriber
from synopsys.adapters.memory import InMemoryEventBus

from .controllers.http.pages import PagesAPIRouter
from .controllers.http.version import get_version


def defaults(
    id_generator: t.Optional[IDGenerator] = None,
    page_repository: t.Optional[PageRepository] = None,
    version_repository: t.Optional[PageVersionRepository] = None,
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[LocalStorageGateway] = None,
) -> t.Tuple[
    IDGenerator,
    PageRepository,
    PageVersionRepository,
    EventBus,
    BlobStorageGateway,
    LocalStorageGateway,
]:
    id_generator = id_generator or ObjectIDGenerator()
    page_repository = page_repository or InMemoryPageRepository()
    version_repository = version_repository or InMemoryPageVersionRepository()
    event_bus = event_bus or InMemoryEventBus()
    blob_storage = blob_storage or InMemoryBlobStorage()
    local_storage = local_storage or TemporaryDirectory()
    return (
        id_generator,
        page_repository,
        version_repository,
        event_bus,
        blob_storage,
        local_storage,
    )


def create_app(
    id_generator: t.Optional[IDGenerator] = None,
    page_repository: t.Optional[PageRepository] = None,
    version_repository: t.Optional[PageVersionRepository] = None,
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[LocalStorageGateway] = None,
    clock: t.Callable[[], int] = lambda: int(time()),
    base_url: str = "http://localhost:8000",
) -> FastAPI:
    """Create  a new Control Plane starlette application.

    Assuming proper arguments are provided, application can be entirely deterministic.
    """
    (
        id_generator,
        page_repository,
        version_repository,
        event_bus,
        blob_storage,
        local_storage,
    ) = defaults(
        id_generator,
        page_repository,
        version_repository,
        event_bus,
        blob_storage,
        local_storage,
    )
    actors = Play(
        bus=event_bus,
        actors=[
            Subscriber(
                event=events.PAGE_DELETED,
                handler=sync_blob.CleanBlobStorageOnPageDelete(storage=blob_storage),
            ),
            Subscriber(
                event=events.PAGE_VERSION_CREATED,
                handler=sync_blob.UploadToBlobStorageOnVersionCreated(
                    event_bus=event_bus, storage=blob_storage
                ),
            ),
            Subscriber(
                event=events.PAGE_VERSION_DELETED,
                handler=sync_blob.CleanBlobStorageOnVersionDelete(storage=blob_storage),
            ),
        ],
    )
    # Need to extend actors because starlette does not start lifespan of mounted apps
    actors.extend(
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
    )
    api_router = PagesAPIRouter(
        id_generator=id_generator,
        versions_repository=version_repository,
        pages_repository=page_repository,
        event_bus=event_bus,
        clock=clock,
    )
    # Create starlette app (ASGI)
    app = FastAPI(
        routes=[
            # API Version
            APIRoute(
                "/api/version",
                get_version,
                methods=["GET"],
                name="get_version",
                include_in_schema=True,
                summary="Get API version",
                description="Returns a JSON object with a 'version' field set to pyhosting server version",
                tags=["Version"],
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
        lifespan=lambda _: actors,
    )
    app.include_router(api_router, prefix="/api/pages", tags=["Pages"])
    return app
