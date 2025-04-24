from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from skylock.api.dependencies import get_current_user, get_skylock_facade
from skylock.api.validation import validate_path_not_empty
from skylock.skylock_facade import SkylockFacade
from skylock.database import models as db_models
from skylock.utils.path import UserPath


router = APIRouter(tags=["Resource", "Download"], prefix="/download")


@router.get(
    "/folders/{path:path}",
    summary="Download a folder",
    description="This endpoint allows users to download a folder as a ZIP file from the specified path.",
    responses={
        200: {
            "description": "Folder downloaded successfully",
            "content": {"application/zip": {}},
        },
        401: {
            "description": "Unauthorized user",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        404: {
            "description": "Folder not found",
            "content": {"application/json": {"example": {"detail": "Folder not found"}}},
        },
    },
)
def download_folder(
    path: str,
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
) -> StreamingResponse:
    folder_data = skylock.download_folder(UserPath(path=path, owner=user))
    return StreamingResponse(
        content=folder_data.data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{folder_data.name}"'},
    )


@router.get(
    "/files/{path:path}",
    summary="Download a file",
    description="This endpoint allows users to download a file from a specified path.",
    responses={
        200: {
            "description": "File downloaded successfully",
            "content": {"application/octet-stream": {}},
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
    },
)
def download_file(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
):
    user_path = UserPath(path=path, owner=user)
    file_data = skylock.download_file(user_path)
    return StreamingResponse(
        content=file_data.data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_data.name}"'},
    )
