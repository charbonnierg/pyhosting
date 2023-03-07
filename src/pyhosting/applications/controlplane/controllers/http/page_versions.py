import typing as t
from dataclasses import asdict

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Router

from pyhosting.domain.gateways import EventBusGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from pyhosting.domain.usecases.crud_pages import GetPage, UpdateLatestPageVersion
from pyhosting.domain.usecases.crud_versions import CreatePageVersion


class PageVersionsRouter(Router):
    def __init__(
        self,
        versions_repository: PageVersionRepository,
        pages_repository: PageRepository,
        event_bus: EventBusGateway,
        clock: t.Callable[[], int],
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.versions_repository = versions_repository
        self.pages_repository = pages_repository
        self.event_bus = event_bus
        self.clock = clock
        self.add_route(
            "/",
            self.create_page_version,
            methods=["POST"],
            name="create_page_version",
        )

    async def create_page_version(self, request: Request) -> JSONResponse:
        """Return an HTTP response indicating whether version was created successfully"""
        # Fetch page version from headers
        version = request.headers.get("x-page-version", None)
        latest = request.headers.get("x-page-latest", None)
        # Return a failure if header is missing
        if version is None:
            return JSONResponse(
                {"error": "x-page-version header must be present"}, status_code=428
            )
        # Prepare usecase (NOTE: This could be done once instead of every request)
        usecase = CreatePageVersion(
            self.versions_repository,
            event_bus=self.event_bus,
            clock=self.clock,
            get_page=GetPage(self.pages_repository),
            update_latest_version=UpdateLatestPageVersion(self.pages_repository),
        )
        # Fetch request body and page id
        content = await request.body()
        page_id = request.path_params["page_id"]
        # Execute usecase
        created_version = await usecase.do(
            page_id=page_id,
            page_version=version,
            content=content,
            latest=latest is not None,
        )
        # Return JSON representation of a page version
        return JSONResponse(asdict(created_version), status_code=201)
