from typing import Annotated

from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from skylock.utils.ratelimit_config import limiter, DEFAULT_RATE_LIMIT

from skylock.pages.dependencies import get_html_bulder, get_templates
from skylock.pages.html_builder import HtmlBuilder
from skylock.utils.exceptions import (
    ForbiddenActionException,
    ResourceNotFoundException,
    InvalidCredentialsException,
)

from skylock.api.dependencies import get_user_service
from skylock.service.user_service import UserService

html_handler = FastAPI(docs_url=None, redoc_url=None)

html_handler.state.limiter = limiter
html_handler.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore[arg-type]


@html_handler.get("/", response_class=HTMLResponse)
def index(request: Request, html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)]):
    return html_builder.build_main_page(request)


@html_handler.get("/folders/{id}", response_class=HTMLResponse)
def folder_contents(
    request: Request,
    id: str,
    html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)],
):
    return html_builder.build_folder_contents_page(request, id)


@html_handler.post("/files/{file_id}/login", response_class=HTMLResponse)
async def login_file_post(
    request: Request,
    file_id: str,
    user_service: Annotated[UserService, Depends(get_user_service)],
    login: str = Form(...),
    password: str = Form(...),
):
    try:
        token = user_service.login_user(login, password)
        user = user_service.user_repository.get_by_username(login)
        response = RedirectResponse(url=f"/files/{file_id}", status_code=302)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token.access_token}",
            httponly=True,
            max_age=3600,
            samesite="lax",
        )
        return response
    except InvalidCredentialsException:
        return templates.TemplateResponse(
            "login_form.html",
            {"request": request, "file_id": file_id, "error": "Invalid credentials"},
            status_code=401,
        )


@html_handler.get("/files/{id}", response_class=HTMLResponse)
def file(
    request: Request,
    id: str,
    html_builder: Annotated[HtmlBuilder, Depends(get_html_bulder)],
):
    return html_builder.build_file_page(request, id)


@html_handler.post("/files/{file_id}/import", response_class=HTMLResponse)
def import_file(file_id: str):
    response = RedirectResponse(url=f"/files/{file_id}", status_code=302)
    response.set_cookie(
        key="import_file", value=file_id, max_age=300, httponly=True, samesite="lax"
    )
    return response


templates = get_templates()


@html_handler.exception_handler(ForbiddenActionException)
async def forbidden_action_exception_handler(request: Request, exc: ForbiddenActionException):
    return templates.TemplateResponse(
        request, "403.html", {"message": exc.message}, status_code=403
    )


@html_handler.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(request: Request, _exc: ResourceNotFoundException):
    return templates.TemplateResponse(request, "404.html", status_code=404)
