import dramatiq
from dramatiq.brokers.redis import RedisBroker

from skylock.config import REDIS_HOST, REDIS_PORT

from skylock.database.session import get_db_session
from skylock.database.repository import (
    FileRepository,
    FolderRepository,
    UserRepository,
    SharedFileRepository,
    LinkRepository,
)
from skylock.service.path_resolver import PathResolver
from skylock.utils.storage import FileStorageService
from skylock.service.resource_service import ResourceService
from skylock.service.zip_service import ZipService
from skylock.utils.path import UserPath
from skylock.api.models import Privacy
from skylock.utils.reddis_mem import redis_mem
from skylock.utils.exceptions import UserNotFoundException

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

redis_broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def create_zip_task(owner_id: str, folder_path: str, force: bool, task_name: str) -> None:
    """Zips a folder and saves it as a new file for the owner.

    This background task creates a ZIP archive of the specified folder's contents
    and stores it as a new private file. It cleans up a task-related Redis entry
    after execution.

    Args:
        owner_id (str): ID of the folder owner.
        folder_path (str): Path to the folder to be zipped.
        force (bool): If True, overwrite if the ZIP file already exists.
        task_name (str): Name of the task for tracking/cleanup in Redis.

    Returns:
        None

    Raises:
        UserNotFoundException: If the owner_id does not correspond to an existing user.
    """
    try:
        db = next(get_db_session())

        file_repo = FileRepository(db)
        folder_repo = FolderRepository(db)
        user_repo = UserRepository(db)
        shared_repo = SharedFileRepository(db)
        link_repo = LinkRepository(db)
        path_resolver = PathResolver(file_repo, folder_repo, user_repo)
        storage = FileStorageService()
        resource_service = ResourceService(
            file_repo, folder_repo, path_resolver, storage, user_repo, shared_repo, link_repo
        )
        zip_service = ZipService(storage)

        user = user_repo.get_by_id(owner_id)
        if not user:
            raise UserNotFoundException
        user_path = UserPath(path=folder_path, owner=user)

        folder = resource_service.get_folder(user_path)

        zip_bytes, size = zip_service.create_zip_from_folder_to_bytes(folder)
        file_path = UserPath(path=folder_path + ".zip", owner=user)
        resource_service.create_file(
            file_path, zip_bytes, size=size, force=force, privacy=Privacy.PRIVATE
        )
    finally:
        redis_mem.delete(task_name)
