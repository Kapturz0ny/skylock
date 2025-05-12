import zipfile
import io
from typing import IO
from skylock.database import models as db_models
from skylock.utils.storage import FileStorageService
from skylock.utils.reddis_mem import redis_mem as s_redis_mem
from skylock.utils.exceptions import ZipQueueError

class ZipService:
    def __init__(self, file_storage_service: FileStorageService, redis_mem=None):
        self._file_storage_service = file_storage_service
        self._redis_mem = redis_mem or s_redis_mem

    def acquire_zip_lock(self, owner_id: int, path: str) -> str:
        task_key = f"zip:{owner_id}:{path}"
        if not self._redis_mem.set(task_key, "queued", nx=True, ex=3600):
            raise ZipQueueError("Zip task already in progress")
        return task_key

    def create_zip_from_folder(self, folder: db_models.FolderEntity) -> IO[bytes]:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            self._add_folder_to_zip(zip_file, folder, "")

        zip_buffer.seek(0)
        return zip_buffer

    def create_zip_from_folder_to_bytes(self, folder: db_models.FolderEntity) -> bytes:
        zip_buffer = self.create_zip_from_folder(folder=folder)
        return zip_buffer.getvalue()


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
            zip_file.writestr(file_path, self._file_storage_service.get_file(file).read())
        for subfolder in folder.subfolders:
            self._add_folder_to_zip(zip_file, subfolder, folder_path)
