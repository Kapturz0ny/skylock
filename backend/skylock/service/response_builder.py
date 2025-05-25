from typing import IO
from skylock.api import models
from skylock.database import models as db_models
from skylock.utils.path import UserPath


class ResponseBuilder:
    """Builds API response models from database entities."""

    def get_folder_contents_response(
        self, folder: db_models.FolderEntity, user_path: UserPath
    ) -> models.FolderContents:
        """Builds a response model for folder contents.

        Args:
            folder: The database folder entity.
            user_path: The user path object for the folder.

        Returns:
            A FolderContents model detailing the folder and its children.
        """
        parent_path = f"/{user_path.path}" if user_path.path else ""
        children_files = [
            models.File(
                id=file.id,
                name=file.name,
                privacy=models.Privacy(file.privacy),
                size=file.size,
                path=f"{parent_path}/{file.name}",
                owner_id=file.owner_id,
            )
            for file in folder.files
        ]
        children_folders = [
            models.Folder(
                id=subfolder.id,
                name=subfolder.name,
                privacy=models.Privacy(subfolder.privacy),
                path=f"{parent_path}/{subfolder.name}",
                type=models.FolderType(subfolder.type),
            )
            for subfolder in folder.subfolders
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
            folder_path=f"/{user_path.path}" if user_path.path else "/",
            files=children_files,
            folders=children_folders,
            links=children_links,
        )

    def get_folder_response(
        self, folder: db_models.FolderEntity, user_path: UserPath
    ) -> models.Folder:
        """Builds a response model for a single folder.

        Args:
            folder: The database folder entity.
            user_path: The user path object for the folder.

        Returns:
            A Folder model representing the folder's metadata.
        """
        return models.Folder(
            id=folder.id,
            name=folder.name,
            path=f"/{user_path.path}" if user_path.path else "/",
            privacy=models.Privacy(folder.privacy),
            type=models.FolderType(folder.type),
        )

    def get_file_response(self, file: db_models.FileEntity, user_path: UserPath) -> models.File:
        """Builds a response model for a single file.

        Args:
            file: The database file entity.
            user_path: The user path object for the file.

        Returns:
            A File model representing the file's metadata.
        """
        return models.File(
            id=file.id,
            name=file.name,
            path=f"/{user_path.path}" if user_path.path else f"/{file.name}",
            size=file.size,
            privacy=models.Privacy(file.privacy),
            owner_id=file.owner_id,
            shared_to=file.shared_to,
        )

    def get_file_data_response(
        self, file: db_models.FileEntity, file_data: IO[bytes]
    ) -> models.FileData:
        """Builds a response model for file data (e.g., download).

        Args:
            file: The database file entity (for metadata).
            file_data: An I/O stream of the file's binary content.

        Returns:
            A FileData model containing the file name and data stream.
        """
        return models.FileData(name=file.name, data=file_data)

    def get_folder_data_response(
        self, folder: db_models.FolderEntity, folder_data: IO[bytes]
    ) -> models.FolderData:
        """Builds a response model for folder data (e.g., ZIP download).

        Args:
            folder: The database folder entity (for metadata).
            folder_data: An I/O stream of the folder's (zipped) binary content.

        Returns:
            A FolderData model containing the folder name (as .zip) and data stream.
        """
        return models.FolderData(name=f"{folder.name}.zip", data=folder_data)
