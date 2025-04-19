from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import ColumnElement

from skylock.database import models

Model = TypeVar("Model", bound=models.Base)


class DatabaseRepository(Generic[Model]):
    def __init__(self, model: Type[Model], session: Session) -> None:
        self.model = model
        self.session = session

    def save(self, entity: Model) -> Model:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Model]:
        return self.session.get(self.model, entity_id)

    def delete(self, entity: Model) -> None:
        self.session.delete(entity)
        self.session.commit()

    def filter(self, *expressions: ColumnElement) -> list[Model]:
        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        return list(self.session.execute(query).scalars())

    def filter_one_or_none(self, *expressions: ColumnElement) -> Optional[Model]:
        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        return self.session.execute(query).scalar_one_or_none()


class UserRepository(DatabaseRepository[models.UserEntity]):
    def __init__(self, session: Session):
        super().__init__(models.UserEntity, session)

    def get_by_username(self, username: str) -> Optional[models.UserEntity]:
        return self.filter_one_or_none(models.UserEntity.username == username)

    def get_by_email(self, email: str) -> Optional[models.UserEntity]:
        return self.filter_one_or_none(models.UserEntity.email == email)


class FolderRepository(DatabaseRepository[models.FolderEntity]):
    def __init__(self, session: Session):
        super().__init__(models.FolderEntity, session)

    def get_by_name_and_parent_id(
        self, name: str, parent_id: str | None
    ) -> Optional[models.FolderEntity]:
        return self.filter_one_or_none(
            models.FolderEntity.parent_folder_id == parent_id,
            models.FolderEntity.name == name,
        )


class FileRepository(DatabaseRepository[models.FileEntity]):
    def __init__(self, session: Session):
        super().__init__(models.FileEntity, session)

    def get_by_name_and_parent(
        self, name: str, parent: models.FolderEntity
    ) -> Optional[models.FileEntity]:
        return self.filter_one_or_none(
            models.FileEntity.name == name, models.FileEntity.folder == parent
        )
    
class SharedFileRepository(DatabaseRepository[models.SharedFileEntity]):
    def __init__(self, session: Session):
        super().__init__(models.SharedFileEntity, session)

    def get_shared_files_by_user_id(
        self, user_id: str
    ) -> list[models.SharedFileEntity]:
        return self.filter(models.SharedFileEntity.user_id == user_id)
    
    def get_shared_files_by_file_id(
        self, file_id: str
    ) -> list[models.SharedFileEntity]:
        return self.filter(models.SharedFileEntity.file_id == file_id)
    
    def is_file_shared_to_user(
        self, file_id: str, user_id: str
    ) -> bool:
        return self.filter_one_or_none(
            models.SharedFileEntity.file_id == file_id,
            models.SharedFileEntity.user_id == user_id,
        ) is not None
