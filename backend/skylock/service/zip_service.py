import zipfile
import io
from skylock.database import models as db_models
from skylock.utils.storage import FileStorageService
from skylock.utils.reddis_mem import redis_mem as s_redis_mem
from skylock.utils.exceptions import ZipQueueError


class ZipService:
    """Handles creation of ZIP archives from folder structures."""

    def __init__(self, file_storage_service: FileStorageService, redis_mem=None):
        """Initializes the ZipService.

        Args:
            file_storage_service: Service for retrieving file contents.
            redis_mem: Optional Redis client for managing task locks.
        """
        self._file_storage_service = file_storage_service
        self._redis_mem = redis_mem or s_redis_mem

    def acquire_zip_lock(self, owner_id: str, path: str) -> str:
        """Attempts to acquire a lock for a zipping task in Redis.

        This prevents multiple zipping operations on the same folder path
        for the same owner from running concurrently.

        Args:
            owner_id: The ID of the user or entity owning the folder.
            path: The path of the folder to be zipped.

        Returns:
            The Redis key used for the lock if acquired successfully.

        Raises:
            ZipQueueError: If a zipping task for the specified owner and path
                           is already in progress or queued.
        """
        task_key = f"zip:{owner_id}:{path}"
        if not self._redis_mem.set(task_key, "queued", nx=True, ex=3600):
            raise ZipQueueError("Zip task already in progress or queued for this folder.")
        return task_key

    def create_zip_from_folder(self, folder: db_models.FolderEntity) -> tuple[io.BytesIO, int]:
        """Creates a ZIP archive from a folder entity in memory.

        The archive is constructed by recursively adding files and subfolders
        from the provided folder entity.

        Args:
            folder: The `db_models.FolderEntity` object representing the root
                    folder to be zipped.

        Returns:
            A tuple containing:
                - An `io.BytesIO` object holding the ZIP archive data.
                - An integer representing the total size of the ZIP archive in bytes.
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            self._add_folder_to_zip(zip_file, folder, "")
        size = zip_buffer.tell()
        zip_buffer.seek(0)  # Reset buffer position to the beginning for reading
        return (zip_buffer, size)

    def create_zip_from_folder_to_bytes(self, folder: db_models.FolderEntity) -> tuple[bytes, int]:
        """Creates a ZIP archive from a folder entity and returns its content as bytes.

        This is a convenience method that calls `create_zip_from_folder` and then
        extracts the byte content from the `io.BytesIO` buffer.

        Args:
            folder: The `db_models.FolderEntity` object representing the root
                    folder to be zipped.

        Returns:
            A tuple containing:
                - A `bytes` object holding the ZIP archive data.
                - An integer representing the total size of the ZIP archive in bytes.
        """
        zip_buffer, size = self.create_zip_from_folder(folder=folder)
        return (zip_buffer.getvalue(), size)

    def _add_folder_to_zip(
        self,
        zip_file: zipfile.ZipFile,
        folder: db_models.FolderEntity,
        current_path: str,
    ):
        """Recursively adds a folder and its contents to an open ZipFile object.

        (Private helper method)

        Args:
            zip_file: The `zipfile.ZipFile` object to which contents are added.
            folder: The `db_models.FolderEntity` currently being processed.
            current_path: The path string representing the location of the `folder`
                          within the ZIP archive.
        """
        folder_path = f"{current_path}{folder.name}/"

        if not folder.files and not folder.subfolders:
            zip_file.writestr(folder_path, "")

        for file in folder.files:
            file_path_in_zip = f"{folder_path}{file.name}"
            file_content_stream = self._file_storage_service.get_file(file)
            zip_file.writestr(file_path_in_zip, file_content_stream.read())
            if hasattr(file_content_stream, "close"):
                file_content_stream.close()

        for subfolder in folder.subfolders:
            self._add_folder_to_zip(zip_file, subfolder, folder_path)
