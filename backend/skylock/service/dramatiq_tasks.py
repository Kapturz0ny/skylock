import dramatiq
from dramatiq.brokers.redis import RedisBroker

from skylock.config import REDIS_HOST, REDIS_PORT

from skylock.database.session import get_db_session
from skylock.database.repository import (
    FileRepository, FolderRepository, UserRepository,
    SharedFileRepository, LinkRepository
)
from skylock.service.path_resolver import PathResolver
from skylock.utils.storage import FileStorageService
from skylock.service.resource_service import ResourceService
from skylock.service.zip_service import ZipService
from skylock.utils.path import UserPath
from skylock.database import models as db_models
from skylock.api.models import Privacy

# temp setup
redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}"

redis_broker = RedisBroker(url=redis_url)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def create_zip_task(owner_id: int, folder_path: str, force: bool) -> None:
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
    user_path = UserPath(path=folder_path, owner=user)

    folder = resource_service.get_folder(user_path)

    zip_bytes = zip_service.create_zip_from_folder_to_bytes(folder)
    file_path = UserPath(path=folder_path + ".zip", owner=user)
    resource_service.create_file(file_path, zip_bytes, force=force, privacy=Privacy.PRIVATE)
