from typing import Annotated

from fastapi import APIRouter, Depends, status

from skylock.api import models
from skylock.api.dependencies import get_current_user, get_skylock_facade
from skylock.api.validation import validate_path_not_empty
from skylock.database import models as db_models
from skylock.skylock_facade import SkylockFacade
from skylock.utils.path import UserPath

router = APIRouter(tags=["Resource"], prefix="/folders")


@router.get(
    "/{path:path}",
    summary="Get folder contents",
    description=(
        """
        This endpoint retrieves the contents of a specified folder.
        It returns a list of files and subfolders contained within the folder at the provided path.
        If path is empty, contents of user's root folder will be listed.
        """
    ),
    responses={
        200: {
            "description": "Successful retrieval of folder contents",
            "content": {
                "application/json": {
                    "example": {
                        "files": [
                            {"name": "file1.txt", "path": "/folder/file1.txt"},
                            {"name": "file2.txt", "path": "/folder/file2.txt"},
                        ],
                        "folders": [
                            {"name": "subfolder1", "path": "/folder/subfolder1"},
                            {"name": "subfolder2", "path": "/folder/subfolder2"},
                        ],
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized user",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        404: {
            "description": "Folder not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Resource not found",
                        "missing": "folder_name",
                    }
                }
            },
        },
    },
)
def get_folder_contents(
    path: str,
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
) -> models.FolderContents:
    return skylock.get_folder_contents(UserPath(path=path, owner=user))


@router.post(
    "/{path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new folder",
    description=(
        """
        This endpoint allows the user to create a new folder at the specified path.
        If the folder already exists or the path is invalid, appropriate errors will be raised.
        """
    ),
    responses={
        201: {
            "description": "Folder created successfully",
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
def create_folder(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
):
    skylock.create_folder_for_user(UserPath(path=path, owner=user))
    return {"message": "Folder created"}


@router.delete(
    "/{path:path}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a folder",
    description=(
        """
        This endpoint allows the user to delete a specified folder. The folder must
        be empty to be deleted unless the 'recursive' parameter is set to True,
        which allows for recursive deletion. If the folder contains any files or
        subfolders and 'recursive' is not set, an error will be raised.
        """
    ),
    responses={
        204: {
            "description": "Folder deleted successfully",
        },
        400: {
            "description": "Invalid path provided, most likely empty",
            "content": {"application/json": {"example": {"detail": "Invalid path"}}},
        },
        401: {
            "description": "Unauthorized user",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        403: {
            "description": "Deleting the root folder is forbidden",
            "content": {
                "application/json": {
                    "example": {"detail": "Deleting your root folder is forbidden"}
                }
            },
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
            "description": "Folder not empty",
            "content": {"application/json": {"example": {"detail": "Folder not empty"}}},
        },
    },
)
def delete_folder(
    path: Annotated[str, Depends(validate_path_not_empty)],
    user: Annotated[db_models.UserEntity, Depends(get_current_user)],
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    recursive: bool = False,
):
    skylock.delete_folder(UserPath(path=path, owner=user), is_recursively=recursive)
    return {"message": "Folder deleted"}
