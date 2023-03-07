from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Router

from pyhosting.infrastructure.actors.asyncio import AsyncioActors


class HealthCheckRouter(Router):
    def __init__(
        self,
        actors: AsyncioActors,
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.actors = actors
        self.add_route("/", self.get_health, methods=["GET"], name="health")

    def get_health(self, _: Request) -> JSONResponse:
        return JSONResponse(
            {"status": "ok" if self.actors.get_first_exception() is None else "ko"}
        )
