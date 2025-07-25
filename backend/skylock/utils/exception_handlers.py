from fastapi.requests import Request
from fastapi.responses import JSONResponse

from skylock.utils.exceptions import (
    FolderNotEmptyException,
    InvalidCredentialsException,
    UserNotFoundException,
    ResourceAlreadyExistsException,
    UserAlreadyExists,
    InvalidPathException,
    ResourceNotFoundException,
    ForbiddenActionException,
    Wrong2FAException,
    EmailAuthenticationError,
    EmailServiceUnavailable,
    ZipQueueError,
)


def user_already_exists_handler(_request: Request, exc: UserAlreadyExists) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


def invalid_credentials_handler(
    _request: Request, exc: InvalidCredentialsException
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


def user_not_found_handler(_request: Request, exc: UserNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


def resource_already_exists_handler(
    _request: Request, exc: ResourceAlreadyExistsException
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


def invalid_path_handler(_request: Request, exc: InvalidPathException) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


def resource_not_found_handler(_request: Request, exc: ResourceNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "missing": exc.missing_resource_name},
    )


def folder_not_empty_handler(_request: Request, exc: FolderNotEmptyException) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc)},
    )


def forbidden_action_handler(_request: Request, exc: ForbiddenActionException) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc)},
    )


def wrong_code_handler(_request: Request, exc: Wrong2FAException) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


def email_authentication_error_handler(
    _request: Request, exc: EmailAuthenticationError
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
        },
    )


def email_service_unavailable_handler(
    _request: Request, exc: EmailServiceUnavailable
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
        },
    )


def zip_queue_error_handler(_request: Request, exc: ZipQueueError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "detail": str(exc),
        },
    )
