import typing as t

from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from genid import IDGenerator
from starlette import status

from pyhosting.core.interfaces import EventBus
from pyhosting.domain.errors import PageAlreadyExistsError, PageNotFoundError
from pyhosting.domain.repositories import PageRepository, PageVersionRepository
from pyhosting.domain.usecases.crud_pages import (
    CreatePage,
    DeletePage,
    GetPage,
    ListPages,
)

from .models.pages import (
    CreatePageOptions,
    CreatePageResult,
    GetPageResult,
    ListPagesResult,
)
from .page_versions import PageVersionsRouter


class PagesAPIRouter(APIRouter):
    def __init__(
        self,
        id_generator: IDGenerator,
        versions_repository: PageVersionRepository,
        pages_repository: PageRepository,
        event_bus: EventBus,
        clock: t.Callable[[], int],
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.id_generator = id_generator
        self.versions_repository = versions_repository
        self.pages_repository = pages_repository
        self.event_bus = event_bus
        self.clock = clock
        # Prepare usecase
        self.get_page_usecase = GetPage(
            repository=self.pages_repository,
        )
        self.create_page_usecase = CreatePage(
            id_generator=self.id_generator,
            repository=self.pages_repository,
            event_bus=self.event_bus,
        )
        self.delete_page_usecase = DeletePage(
            repository=self.pages_repository,
            event_bus=self.event_bus,
        )
        self.list_pages_usecase = ListPages(
            repository=self.pages_repository,
        )
        # Setup routes
        self.setup()

    def setup(self) -> None:
        self.add_api_route(
            "/",
            self.list_pages,
            methods=["GET"],
            name="list_pages",
            response_model=ListPagesResult,
        )
        self.add_api_route(
            "/",
            self.create_page,
            methods=["POST"],
            name="create_page",
            response_model=CreatePageResult,
            status_code=201,
            responses={"409": {"description": "Page with same name already exist"}},
        )
        self.add_api_route(
            "/{page_id}",
            self.get_page,
            methods=["GET"],
            name="get_page",
            response_model=GetPageResult,
        )
        self.add_api_route(
            "/{page_id}",
            self.delete_page,
            methods=["DELETE"],
            name="delete_page",
            status_code=204,
        )
        self.include_router(
            PageVersionsRouter(
                versions_repository=self.versions_repository,
                pages_repository=self.pages_repository,
                event_bus=self.event_bus,
                clock=self.clock,
            ),
            prefix="/{page_id}/versions",
        )

    async def get_page(self, page_id: str) -> GetPageResult:
        """Get page infos."""
        # Execute usecase
        try:
            page = await self.get_page_usecase.do(page_id=page_id)
        except PageNotFoundError as exc:
            # Return an HTTP response with a failure code
            raise HTTPException(detail={"error": exc.msg}, status_code=exc.code)
        # Return JSON representation of a page
        result = GetPageResult(document=page)
        # I don't understand how FastAPI works...
        return result.dict()  # type: ignore[return-value]

    async def list_pages(self) -> ListPagesResult:
        """List existing pages."""
        # Execute usecase
        pages = await self.list_pages_usecase.do()
        # Return a JSON response
        result = ListPagesResult(documents=pages)
        # I don't understand how FastAPI works
        return result.dict()  # type: ignore[return-value]

    async def create_page(self, options: CreatePageOptions) -> CreatePageResult:
        """Return an HTTP response with either a page creation success or page creation a failure"""
        # Execute usecase with command
        try:
            page = await self.create_page_usecase.do(
                name=options.name,
                title=options.title,
                description=options.description,
            )
        except PageAlreadyExistsError as exc:
            # Return an HTTP response with failure code
            raise HTTPException(
                detail={"error": exc.msg}, status_code=status.HTTP_409_CONFLICT
            )
        # Return create page ID
        result = CreatePageResult(document=page)
        # I don't understand how FastAPI works
        return result.dict()  # type: ignore[return-value]

    async def delete_page(self, page_id: str) -> None:
        """Return an HTTP response without content upon page deletion"""
        # Execute usecase with command
        try:
            await self.delete_page_usecase.do(page_id=page_id)
        except PageNotFoundError as exc:
            # Return an HTTP error when page does not exist
            raise HTTPException(
                detail={"error": exc.msg}, status_code=status.HTTP_404_NOT_FOUND
            )
