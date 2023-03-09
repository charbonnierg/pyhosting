from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Router

from pyhosting.core.aio import Actors


class HealthCheckRouter(Router):
    def __init__(
        self,
        actors: Actors,
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.actors = actors
        self.add_route("/", self.get_health, methods=["GET"], name="health")

    def get_health(self, _: Request) -> JSONResponse:
        ok = self.actors.started() and not self.actors.done()
        return JSONResponse({"status": "ok" if ok else "ko"})
