from starlette.requests import Request
from starlette.responses import JSONResponse

from pyhosting import __version__


async def get_version(_: Request) -> JSONResponse:
    """Return an HTTP response with pyhosting version."""
    return JSONResponse({"version": __version__}, status_code=200)
