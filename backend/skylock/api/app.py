from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from skylock.utils.ratelimit_config import limiter

from skylock.api.routes import (
    auth_routes,
    download_routes,
    file_routes,
    folder_routes,
    shared_routes,
    share_routes,
    upload_routes,
    zip_routes,
)
from skylock.utils.exception_handlers import (
    folder_not_empty_handler,
    forbidden_action_handler,
    invalid_credentials_handler,
    user_not_found_handler,
    resource_already_exists_handler,
    resource_not_found_handler,
    user_already_exists_handler,
    wrong_code_handler,
    invalid_path_handler,
    email_authentication_error_handler,
    email_service_unavailable_handler,
    zip_queue_error_handler,
)
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    InvalidCredentialsException,
    UserNotFoundException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    UserAlreadyExists,
    Wrong2FAException,
    InvalidPathException,
    EmailAuthenticationError,
    EmailServiceUnavailable,
    ZipQueueError,
)

api = FastAPI(title="File Sharing API", version="1.0.0")
api.state.limiter = limiter
api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

api.add_exception_handler(UserAlreadyExists, user_already_exists_handler)  # type: ignore[arg-type]
api.add_exception_handler(InvalidCredentialsException, invalid_credentials_handler)  # type: ignore[arg-type]
api.add_exception_handler(UserNotFoundException, user_not_found_handler)  # type: ignore[arg-type]
api.add_exception_handler(ResourceAlreadyExistsException, resource_already_exists_handler)  # type: ignore[arg-type]
api.add_exception_handler(ResourceNotFoundException, resource_not_found_handler)  # type: ignore[arg-type]
api.add_exception_handler(FolderNotEmptyException, folder_not_empty_handler)  # type: ignore[arg-type]
api.add_exception_handler(ForbiddenActionException, forbidden_action_handler)  # type: ignore[arg-type]
api.add_exception_handler(Wrong2FAException, wrong_code_handler)  # type: ignore[arg-type]
api.add_exception_handler(InvalidPathException, invalid_path_handler)  # type: ignore[arg-type]
api.add_exception_handler(EmailAuthenticationError, email_authentication_error_handler)  # type: ignore[arg-type]
api.add_exception_handler(EmailServiceUnavailable, email_service_unavailable_handler)  # type: ignore[arg-type]
api.add_exception_handler(ZipQueueError, zip_queue_error_handler)  # type: ignore[arg-type]


api.include_router(auth_routes.router)
api.include_router(folder_routes.router)
api.include_router(file_routes.router)
api.include_router(shared_routes.router)
api.include_router(share_routes.router)
api.include_router(download_routes.router)
api.include_router(upload_routes.router)
api.include_router(zip_routes.router)
