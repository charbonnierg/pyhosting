import logging
import typing as t
from time import time

from fastapi import FastAPI
from fastapi.routing import APIRoute
from genid import IDGenerator
from starlette.routing import Mount

from pyhosting.adapters.instrumentation import PlayInstrumentation
from pyhosting.applications.dataplane.factory import create_app as create_agent_app
from pyhosting.domain import events
from pyhosting.domain.gateways import (
    BlobStorageGateway,
    FilestorageGateway,
    TemplateLoader,
)
from pyhosting.domain.repositories import PageRepository
from pyhosting.domain.usecases.effects import pages_control_plane, pages_data_plane
from synopsys import EventBus, Play, Subscriber

from .defaults import defaults
from .routes.http.api_version import get_version
from .routes.http.pages import PagesAPIRouter


def create_app(
    id_generator: t.Optional[IDGenerator] = None,
    page_repository: t.Optional[PageRepository] = None,
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[FilestorageGateway] = None,
    templates: t.Optional[TemplateLoader] = None,
    clock: t.Callable[[], int] = lambda: int(time()),
    base_url: str = "http://localhost:8000",
) -> FastAPI:
    """Create  a new Control Plane starlette application.

    Assuming proper arguments are provided, application can be entirely deterministic.
    """
    instrumentation = PlayInstrumentation()
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s - %(message)s",
    )
    (
        id_generator,
        page_repository,
        event_bus,
        blob_storage,
        local_storage,
        templates,
        clock,
    ) = defaults(
        id_generator,
        page_repository,
        event_bus,
        blob_storage,
        local_storage,
        templates,
        clock,
    )
    actors = Play(
        bus=event_bus,
        actors=[
            Subscriber(
                event=events.PAGE_DELETED,
                handler=pages_control_plane.CleanStorageOnPageDeleted(
                    storage=blob_storage
                ),
            ),
            Subscriber(
                event=events.VERSION_CREATED,
                handler=pages_control_plane.UploadContentOnVersionCreated(
                    event_bus=event_bus, storage=blob_storage
                ),
            ),
            Subscriber(
                event=events.VERSION_DELETED,
                handler=pages_control_plane.CleanStorageOnVersionDeleted(
                    storage=blob_storage
                ),
            ),
        ],
        instrumentation=instrumentation,
        auto_connect=True,
    )
    # Need to extend actors because starlette does not start lifespan of mounted apps
    actors.extend(
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
    )
    api_router = PagesAPIRouter(
        id_generator=id_generator,
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
                    blob_storage=blob_storage,
                    local_storage=local_storage,
                    base_url=base_url,
                ),
            ),
        ],
        lifespan=lambda _: actors,
    )
    app.include_router(api_router, prefix="/api/pages", tags=["Pages"])

    return app
