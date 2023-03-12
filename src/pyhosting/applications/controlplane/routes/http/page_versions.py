import typing as t

from fastapi import HTTPException
from fastapi.routing import APIRouter
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from pyhosting.domain.errors import EmptyContentError, ResourceNotFoundError
from pyhosting.domain.repositories import PageRepository
from pyhosting.domain.usecases import commands, queries
from synopsys import EventBus

from .models.pages import (
    CreatePageVersionResult,
    GetPageVersionResult,
    ListPageVersionsResult,
)


class PageVersionsRouter(APIRouter):
    def __init__(
        self,
        pages_repository: PageRepository,
        event_bus: EventBus,
        clock: t.Callable[[], int],
    ) -> None:
        super().__init__(redirect_slashes=True, tags=["Pages Versions"])
        self.pages_repository = pages_repository
        self.event_bus = event_bus
        self.clock = clock
        # Prepare usecases
        self.get_page_usecase = queries.pages.GetPage(self.pages_repository)
        self.create_usecase = commands.pages.PublishVersion(
            page_repository=self.pages_repository,
            event_bus=self.event_bus,
            clock=self.clock,
        )
        self.get_usecase = queries.pages.GetPageVersion(
            page_repository=self.pages_repository,
        )
        self.delete_usecase = commands.pages.DeletePageVersion(
            page_repository=self.pages_repository,
            event_bus=self.event_bus,
        )
        self.list_usecase = queries.pages.ListPagesVersions(
            page_repository=self.pages_repository,
        )
        self.setup()

    def setup(self) -> None:
        self.add_api_route(
            "/",
            self.create_page_version,
            methods=["POST"],
            name="create_page_version",
            response_model=CreatePageVersionResult,
            response_class=JSONResponse,
        )
        self.add_api_route(
            "/{page_version}",
            self.get_page_version,
            methods=["GET"],
            name="get_page_version",
            response_model=GetPageVersionResult,
            response_class=JSONResponse,
        )
        self.add_api_route(
            "/{page_version}",
            self.delete_page_version,
            methods=["DELETE"],
            name="delete_page_version",
            response_model=None,
            status_code=204,
        )
        self.add_api_route(
            "/",
            self.list_page_versions,
            methods=["GET"],
            name="list_page_versions",
            response_model=ListPageVersionsResult,
        )

    async def get_page_version(
        self, page_id: str, page_version: str
    ) -> GetPageVersionResult:
        """Get info about page version."""
        try:
            version = await self.get_usecase(page_id=page_id, page_version=page_version)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=exc.code, detail={"error": exc.msg})
        result = GetPageVersionResult(document=version)
        # I don't understand how FastAPI works...
        return result.dict()  # type: ignore[return-value]

    async def delete_page_version(
        self,
        page_id: str,
        page_version: str,
    ) -> None:
        """Delete a page version"""
        try:
            await self.delete_usecase(page_id=page_id, page_version=page_version)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=exc.code, detail={"error": exc.msg})

    async def list_page_versions(self, page_id: str) -> ListPageVersionsResult:
        """List versions for a page"""
        try:
            versions = await self.list_usecase(page_id=page_id)
        except ResourceNotFoundError as exc:
            raise HTTPException(status_code=exc.code, detail={"error": exc.msg})
        result = ListPageVersionsResult(documents=versions)
        # I don't understand how FastAPI works...
        return result.dict()  # type: ignore[return-value]

    async def create_page_version(
        self, request: Request, page_id: str
    ) -> CreatePageVersionResult:
        """Return an HTTP response indicating whether version was created successfully"""
        # Note: page_id is extracted from path parameter
        # Fetch page version from headers
        version = request.headers.get("x-page-version", None)
        latest = request.headers.get("x-page-latest", None)
        # Return a failure if header is missing
        if version is None:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail={"error": "x-page-version header must be present"},
            )
        # Fetch request body and page id
        content = await request.body()
        # Execute usecase
        try:
            created_version = await self.create_usecase(
                page_id=page_id,
                page_version=version,
                content=content,
                latest=latest is not None,
            )
        except EmptyContentError as exc:
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail={"error": exc.msg},
            )
        # Return result
        result = CreatePageVersionResult(document=created_version)
        # I don't understand how FastAPI works...
        return result.dict()  # type: ignore[return-value]
