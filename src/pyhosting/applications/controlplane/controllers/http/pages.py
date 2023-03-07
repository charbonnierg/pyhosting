import typing as t
from dataclasses import asdict

from genid import IDGenerator
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Router

from pyhosting.domain.errors import PageAlreadyExistsError, PageNotFoundError
from pyhosting.domain.gateways import EventBusGateway
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from pyhosting.domain.usecases.crud_pages import (
    CreatePage,
    DeletePage,
    GetPage,
    ListPages,
)

from .page_versions import PageVersionsRouter


class PagesAPIRouter(Router):
    def __init__(
        self,
        id_generator: IDGenerator,
        versions_repository: PageVersionRepository,
        pages_repository: PageRepository,
        event_bus: EventBusGateway,
        clock: t.Callable[[], int],
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.id_generator = id_generator
        self.versions_repository = versions_repository
        self.pages_repository = pages_repository
        self.event_bus = event_bus
        self.clock = clock
        self.add_route("/", self.list_pages, methods=["GET"], name="list_pages")
        self.add_route("/", self.create_page, methods=["POST"], name="create_page")
        self.add_route("/{page_id}", self.get_page, methods=["GET"], name="get_page")
        self.add_route(
            "/{page_id}", self.delete_page, methods=["DELETE"], name="delete_page"
        )
        self.mount(
            "/{page_id}/versions",
            PageVersionsRouter(
                versions_repository=self.versions_repository,
                pages_repository=self.pages_repository,
                event_bus=event_bus,
                clock=clock,
            ),
        )

    async def get_page(self, request: Request) -> JSONResponse:
        """Reutrn an HTTP response with an existing page infos."""
        # Prepare usecase
        usecase = GetPage(repository=self.pages_repository)
        # Extract path parameter
        page_id = request.path_params["page_id"]
        # Execute usecase
        try:
            result = await usecase.do(page_id=page_id)
        except PageNotFoundError as exc:
            # Return an HTTP error rather than raising an exception
            return JSONResponse({"error": exc.msg}, status_code=exc.code)
        # Return JSON representation of a page
        return JSONResponse(asdict(result), status_code=200)

    async def list_pages(self, _: Request) -> JSONResponse:
        """Return an HTTP response with a list of existing pages."""
        # Prepare usecase
        usecase = ListPages(repository=self.pages_repository)
        # Execute usecase
        pages = await usecase.do()
        # Return a JSON response
        return JSONResponse(
            {"pages": [asdict(page) for page in pages]}, status_code=200
        )

    async def create_page(self, request: Request) -> JSONResponse:
        """Return an HTTP response with either a page creation success or page creation a failure"""
        # Prepare usecase
        usecase = CreatePage(
            id_generator=self.id_generator,
            repository=self.pages_repository,
            event_bus=self.event_bus,
        )
        # Fetch request body
        command = await request.json()
        # Execute usecase with command
        try:
            result = await usecase.do(
                name=command["name"],
                title=command.get("title"),
                description=command.get("description"),
            )
        except PageAlreadyExistsError as exc:
            # Return an HTTP error instead of raising an exception
            return JSONResponse({"error": exc.msg}, status_code=409)
        # Return create page ID
        return JSONResponse({"id": result.id}, status_code=201)

    async def delete_page(self, request: Request) -> t.Union[Response, JSONResponse]:
        """Return an HTTP response without content upon page deletion"""
        # Prepare usecase
        usecase = DeletePage(
            repository=self.pages_repository,
            event_bus=self.event_bus,
        )
        # Prepare command using path parameter
        page_id = request.path_params["page_id"]
        # Execute usecase with command
        try:
            await usecase.do(page_id=page_id)
        except PageNotFoundError as exc:
            # Return an HTTP error when page does not exist
            return JSONResponse({"error": exc.msg}, status_code=exc.code)
        # Return an empty HTTP response with 204 status code
        return Response(b"", status_code=204)
