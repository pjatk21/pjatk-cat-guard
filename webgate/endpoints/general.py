import os

from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request

from webgate.common import templates


class AboutPage(HTTPEndpoint):
    async def get(self, request: Request):
        return templates.TemplateResponse(
            "home.html", {"request": request, "invitation": os.getenv("INVITATION")}
        )
