import zipfile
import io
from typing import IO
from skylock.database import models as db_models
from skylock.utils.storage import FileStorageService


class ZipService:
    def __init__(self, file_storage_service: FileStorageService):
        self._file_storage_service = file_storage_service

    def create_zip_from_folder(self, folder: db_models.FolderEntity) -> IO[bytes]:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            self._add_folder_to_zip(zip_file, folder, "")

        zip_buffer.seek(0)
        return zip_buffer

    def _add_folder_to_zip(
        self,
        zip_file: zipfile.ZipFile,
        folder: db_models.FolderEntity,
        current_path: str,
    ):
        folder_path = f"{current_path}{folder.name}/"

        if not folder.files and not folder.subfolders:
            zip_file.writestr(folder_path, "")

        for file in folder.files:
            file_path = f"{folder_path}{file.name}"
            zip_file.writestr(
                file_path, self._file_storage_service.get_file(file).read()
            )
        for subfolder in folder.subfolders:
            self._add_folder_to_zip(zip_file, subfolder, folder_path)
