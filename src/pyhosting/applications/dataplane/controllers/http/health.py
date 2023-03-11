from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Router

from synopsys import Play


class HealthCheckRouter(Router):
    def __init__(
        self,
        play: Play,
    ) -> None:
        super().__init__(redirect_slashes=True)
        self.play = play
        self.add_route("/", self.get_health, methods=["GET"], name="health")

    def get_health(self, _: Request) -> JSONResponse:
        ok = self.play.started() and not self.play.done()
        return JSONResponse({"status": "ok" if ok else "ko"})
