from fastapi import FastAPI

from skylock.api.routes import (
    auth_routes,
    file_routes,
    folder_routes,
    public_routes,
    share_routes,
)
from skylock.utils.exception_handlers import (
    folder_not_empty_handler,
    forbidden_action_handler,
    invalid_credentials_handler,
    resource_already_exists_handler,
    resource_not_found_handler,
    user_already_exists_handler,
)
from skylock.utils.exceptions import (
    FolderNotEmptyException,
    ForbiddenActionException,
    InvalidCredentialsException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
    UserAlreadyExists,
)

api = FastAPI(title="File Sharing API", version="1.0.0")


api.add_exception_handler(UserAlreadyExists, user_already_exists_handler)
api.add_exception_handler(InvalidCredentialsException, invalid_credentials_handler)
api.add_exception_handler(ResourceAlreadyExistsException, resource_already_exists_handler)
api.add_exception_handler(ResourceNotFoundException, resource_not_found_handler)
api.add_exception_handler(FolderNotEmptyException, folder_not_empty_handler)
api.add_exception_handler(ForbiddenActionException, forbidden_action_handler)


api.include_router(auth_routes.router)
api.include_router(folder_routes.router)
api.include_router(file_routes.router)
api.include_router(public_routes.router)
api.include_router(share_routes.router)
