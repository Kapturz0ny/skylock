from typing import Annotated

from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from skylock.utils.ratelimit_config import limiter, DEFAULT_RATE_LIMIT

from skylock.pages.dependencies import get_html_builder, get_templates
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
html_handler.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

templates = get_templates()


@html_handler.get(
    "/",
    response_class=HTMLResponse,
    summary="Display the main page.",
    description=(
        """
        Serves the main landing page of the application.
        This endpoint provides the initial HTML view for users visiting the root URL.
        """
    ),
)
def index(request: Request, html_builder: Annotated[HtmlBuilder, Depends(get_html_builder)]):
    return html_builder.build_main_page(request)


@html_handler.get(
    "/folders/{id}",
    response_class=HTMLResponse,
    summary="Display contents of a specific folder.",
    description=(
        """
        Retrieves and displays the publicly accessible files and subfolders
        within the folder specified by its ID.
        """
    ),
)
def folder_contents(
    request: Request,
    id: str,
    html_builder: Annotated[HtmlBuilder, Depends(get_html_builder)],
):
    return html_builder.build_folder_contents_page(request, id)


@html_handler.post(
    "/files/{file_id}/login",
    response_class=HTMLResponse,
    summary="Authenticate user to access a specific file.",
    description=(
        """
        Handles user login attempts specifically for accessing a file.
        Accepts 'login' and 'password' form data.
        If credentials are valid, it sets an 'access_token' cookie and redirects
        the user to the file page.
        Returns an error page for invalid credentials or if rate limits are exceeded.
        """
    ),
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def login_file_post(
    request: Request,
    file_id: str,
    user_service: Annotated[UserService, Depends(get_user_service)],
    login: str = Form(...),
    password: str = Form(...),
):
    try:
        token = user_service.login_user(login, password)
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
    except RateLimitExceeded:
        return templates.TemplateResponse(
            "login_form.html",
            {
                "request": request,
                "file_id": file_id,
                "error": "Too many requests. Try again later.",
            },
            status_code=429,
        )


@html_handler.get(
    "/files/{id}",
    response_class=HTMLResponse,
    summary="Display a specific file page.",
    description=(
        """
        Serves the HTML page for a specific file identified by its ID.
        Access control (e.g., checking for public, protected, or private status,
        and user authentication/authorization) is handled by the HtmlBuilder,
        which may render the file details or a login page.
        """
    ),
)
def file(
    request: Request,
    id: str,
    html_builder: Annotated[HtmlBuilder, Depends(get_html_builder)],
):
    return html_builder.build_file_page(request, id)


@html_handler.post(
    "/files/{file_id}/import",
    response_class=HTMLResponse,
    summary="Mark a file for import.",
    description=(
        """
        Sets a cookie ('import_file') to indicate that the user intends to import
        the specified file. This is typically used as part of a workflow where a user
        views a public file and then decides to import it into their own resources,
        often requiring login. The cookie helps retain context.
        Redirects back to the file page.
        """
    ),
)
def import_file(file_id: str):
    response = RedirectResponse(url=f"/files/{file_id}", status_code=302)
    response.set_cookie(
        key="import_file", value=file_id, max_age=300, httponly=True, samesite="lax"
    )
    return response


@html_handler.exception_handler(ForbiddenActionException)
async def forbidden_action_exception_handler(request: Request, exc: ForbiddenActionException):
    """Handles ForbiddenActionException and returns a custom 403 HTML error page.

    Args:
        request (Request): The incoming HTTP request.
        exc (ForbiddenActionException): The raised exception instance.

    Returns:
        HTMLResponse: A rendered 403 error page.
    """
    return templates.TemplateResponse(
        request, "403.html", {"message": exc.message}, status_code=403
    )


@html_handler.exception_handler(ResourceNotFoundException)
async def resource_not_found_exception_handler(request: Request, _exc: ResourceNotFoundException):
    """Handles ResourceNotFoundException and returns a custom 404 HTML error page.

    Args:
        request (Request): The incoming HTTP request.
        _exc (ResourceNotFoundException): The raised exception instance (not used in response).

    Returns:
        HTMLResponse: A rendered 404 error page.
    """
    return templates.TemplateResponse(request, "404.html", status_code=404)
