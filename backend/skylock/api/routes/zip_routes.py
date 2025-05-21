from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import StreamingResponse

from skylock.api import models
from skylock.api.dependencies import get_current_user, get_skylock_facade
from skylock.api.validation import validate_path_not_empty
from skylock.database import models as db_models
from skylock.skylock_facade import SkylockFacade
from skylock.utils.path import UserPath
from skylock.utils.exceptions import ResourceAlreadyExistsException


from skylock.utils.logger import logger

router = APIRouter(tags=["Resource"], prefix="/zip")

@router.post(
    "/{path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new zip file out of folder",
    description=(
        """
        This endpoint allows the user to create a new zip file out of a folder at the specified path.
        If the zip file already exists or the path is invalid, appropriate errors will be raised.
        """
    ),
    responses={
        201: {
            "description": "Zip file created successfully",
            "content": {"application/json": {"example": {"message": "Folder created"}}},
        },
        400: {
            "description": "Invalid path provided, most likely empty",
            "content": {"application/json": {"example": {"detail": "Invalid path"}}},
        },
        401: {
            "description": "Unauthorized user",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        404: {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Resource not found",
                        "missing": "folder_name",
                    }
                }
            },
        },
        409: {
            "description": "Resource already exists",
            "content": {"application/json": {"example": {"detail": "Resource already exists"}}},
        },
    },
)
def zip_folder(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    force: bool,
) -> dict:
    try:
        task_id = skylock.create_zip(
        UserPath(path=path, owner=user), force
    )
    except ResourceAlreadyExistsException as exc:
        raise HTTPException(status_code=409, message=str(exc))
    return {"task_id": task_id, "message": "queued"}