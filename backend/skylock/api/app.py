from fastapi import FastAPI, Depends
from slowapi import _rate_limit_exceeded_handler # Handler dla wyjątków
from slowapi.errors import RateLimitExceeded # Sam wyjątek
from skylock.utils.ratelimit_config import limiter as global_limiter, DEFAULT_RATE_LIMIT

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
    resource_already_exists_handler,
    resource_not_found_handler,
    user_already_exists_handler,
    wrong_code_handler,
    invalid_path_handler,
    email_authentication_error_handler,
    email_service_unavailable_handler,
)
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    InvalidCredentialsException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    UserAlreadyExists,
    Wrong2FAException,
    InvalidPathException,
    EmailAuthenticationError,
    EmailServiceUnavailable,
)

api = FastAPI(title="File Sharing API", version="1.0.0")#, dependencies=[Depends(global_limiter.limit(DEFAULT_RATE_LIMIT))])
api.state.limiter = global_limiter # Użyj globalnego limitera
api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api.add_exception_handler(UserAlreadyExists, user_already_exists_handler)
api.add_exception_handler(InvalidCredentialsException, invalid_credentials_handler)
api.add_exception_handler(ResourceAlreadyExistsException, resource_already_exists_handler)
api.add_exception_handler(ResourceNotFoundException, resource_not_found_handler)
api.add_exception_handler(FolderNotEmptyException, folder_not_empty_handler)
api.add_exception_handler(ForbiddenActionException, forbidden_action_handler)
api.add_exception_handler(Wrong2FAException, wrong_code_handler)
api.add_exception_handler(InvalidPathException, invalid_path_handler)
api.add_exception_handler(EmailAuthenticationError, email_authentication_error_handler)
api.add_exception_handler(EmailServiceUnavailable, email_service_unavailable_handler)


api.include_router(auth_routes.router)
api.include_router(folder_routes.router)
api.include_router(file_routes.router)
api.include_router(shared_routes.router)
api.include_router(share_routes.router)
api.include_router(download_routes.router)
api.include_router(upload_routes.router)
api.include_router(zip_routes.router)
