from typing import IO
from skylock.api import models
from skylock.database import models as db_models
from skylock.utils.path import UserPath


class ResponseBuilder:
    def get_folder_contents_response(
        self, folder: db_models.FolderEntity, user_path: UserPath
    ) -> models.FolderContents:
        parent_path = f"/{user_path.path}" if user_path.path else ""
        children_files = [
            models.File(
                id=file.id,
                name=file.name,
                privacy=file.privacy,
                size=file.size,
                path=f"{parent_path}/{file.name}",
                owner_id=file.owner_id,
            )
            for file in folder.files
        ]
        children_folders = [
            models.Folder(
                id=folder.id,
                name=folder.name,
                privacy=folder.privacy,
                path=f"{parent_path}/{folder.name}",
                type=folder.type,
            )
            for folder in folder.subfolders
        ]
        children_links = [
            models.Link(
                id=link.id,
                name=link.name,
                path=f"{parent_path}/{link.name}",
            )
            for link in folder.links
        ]
        return models.FolderContents(
            folder_name=folder.name,
            folder_path=f"/{user_path.path}",
            files=children_files,
            folders=children_folders,
            links=children_links,
        )

    def get_folder_response(
        self, folder: db_models.FolderEntity, user_path: UserPath
    ) -> models.Folder:
        return models.Folder(
            id=folder.id,
            name=folder.name,
            path=f"/{user_path.path}",
            privacy=folder.privacy,
        )

    def get_file_response(self, file: db_models.FileEntity, user_path: UserPath) -> models.File:
        return models.File(
            id=file.id,
            name=file.name,
            path=f"/{user_path.path}",
            size=file.size,
            privacy=file.privacy,
            owner_id=file.owner_id,
            shared_to=file.shared_to,
        )

    def get_file_data_response(
        self, file: db_models.FileEntity, file_data: IO[bytes]
    ) -> models.FileData:
        return models.FileData(name=file.name, data=file_data)

    def get_folder_data_response(
        self, folder: db_models.FolderEntity, folder_data: IO[bytes]
    ) -> models.FolderData:
        return models.FolderData(name=f"{folder.name}.zip", data=folder_data)
