from typing import Annotated

from fastapi import APIRouter, Depends, Response, UploadFile, status
from fastapi.responses import StreamingResponse


from skylock.api.dependencies import get_current_user, get_skylock_facade
from skylock.api.validation import validate_path_not_empty
from skylock.database import models as db_models
from skylock.skylock_facade import SkylockFacade
from skylock.utils.path import UserPath
from skylock.api import models

router = APIRouter(tags=["Resource"], prefix="/files")


@router.post(
    "/upload/{path:path}",
    summary="Upload a file",
    description=(
        """
        This endpoint allows users to upload a file to a specified path.
        If the file already exists, an appropriate error will be raised.
        """
    ),
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "File uploaded successfully",
            "content": {"application/json": {"example": {"message": "File uploaded successfully"}}},
        },
        400: {
            "description": "Invalid path provided, most likely empty",
            "content": {"application/json": {"example": {"detail": "Invalid path"}}},
        },
        401: {
            "description": "Unauthorized user",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        409: {
            "description": "Resource already exists",
            "content": {"application/json": {"example": {"detail": "File already exists"}}},
        },
    },
)
def upload_file(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    file: UploadFile,
    force: bool = False,
    public: bool = False,
) -> models.File:
    return skylock.upload_file(
        user_path=UserPath(path=path, owner=user),
        file_data=file.file.read(),
        force=force,
        public=public,
    )


@router.delete(
    "/{path:path}",
    summary="Delete a file",
    description=(
        """
        This endpoint allows users to delete a file from a specified path.
        The user must own the file or have appropriate permissions.
        If the file does not exist or the path is invalid, an appropriate error will be raised.
        """
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "File deleted successfully",
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
            "description": "File not found",
            "content": {"application/json": {"example": {"detail": "File not found"}}},
        },
        403: {
            "description": "Forbidden action, user is not authorized to delete the file",
            "content": {"application/json": {"example": {"detail": "Forbidden action"}}},
        },
    },
)
def delete_file(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
):
    skylock.delete_file(UserPath(path=path, owner=user))


@router.patch(
    "/{path:path}",
    status_code=status.HTTP_200_OK,
    summary="Change file visablity",
    description=(
        """
        This endpoint allows the user to change the visability of a specified file. 
        Sharing a file opens it up to public access.
        """
    ),
    responses={
        204: {
            "description": "file visablity cahnged successfully",
            "content": {"application/json": {"message": "file visablity changed"}},
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
                        "missing": "file_name",
                    }
                }
            },
        },
    },
)
def change_file_visability(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    request: models.UpdateFileRequest,
) -> models.File:
    return skylock.update_file(UserPath(path=path, owner=user), request.privacy, request.shared)
