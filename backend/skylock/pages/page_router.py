from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse

from skylock.pages.dependencies import get_html_bulder, get_templates
from skylock.pages.html_builder import HtmlBuilder
from skylock.utils.exceptions import ForbiddenActionException, ResourceNotFoundException

html_hanlder = FastAPI(docs_url=None, redoc_url=None)


@html_hanlder.get("/", response_class=HTMLResponse)
def index(request: Request, html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)]):
    return html_builder.build_main_page(request)


@html_hanlder.get("/folders/{id}", response_class=HTMLResponse)
def folder_contents(
    request: Request, id: str, html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)]
):
    return html_builder.build_folder_contents_page(request, id)

@html_hanlder.get("/files/{id}/login", response_class=HTMLResponse)
def login_file(request: Request, id: str, html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)]):
    return html_builder.build_file_page(request, id)


@html_hanlder.get("/files/{id}", response_class=HTMLResponse)
def file(request: Request, id: str, html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)]):
    return html_builder.build_file_page(request, id)

templates = get_templates()


@html_hanlder.exception_handler(ForbiddenActionException)
async def forbidden_action_exception_handler(request: Request, exc: ForbiddenActionException):
    return templates.TemplateResponse(
        request, "403.html", {"message": exc.message}, status_code=403
    )


@html_hanlder.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(request: Request, _exc: ResourceNotFoundException):
    return templates.TemplateResponse(request, "404.html", status_code=404)
