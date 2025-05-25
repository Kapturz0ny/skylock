from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import ColumnElement

from skylock.database import models

Model = TypeVar("Model", bound=models.Base)


class DatabaseRepository(Generic[Model]):
    """Generic repository for database operations on a specific model."""
    def __init__(self, model: Type[Model], session: Session) -> None:
        """Initializes the repository with a model type and a database session.

        Args:
            model (Type[Model]): The SQLAlchemy model class.
            session (Session): The SQLAlchemy session.
        """
        self.model = model
        self.session = session

    def save(self, entity: Model) -> Model:
        """Saves an entity to the database.

        Args:
            entity (Model): The entity instance to save.

        Returns:
            Model: The saved and refreshed entity instance.
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[Model]:
        """Retrieves an entity by its primary key ID.

        Args:
            entity_id (str): The ID of the entity to retrieve.

        Returns:
            Optional[Model]: The entity instance if found, otherwise None.
        """
        return self.session.get(self.model, entity_id)

    def delete(self, entity: Model) -> None:
        """Deletes an entity from the database.

        Args:
            entity (Model): The entity instance to delete.
        """
        self.session.delete(entity)
        self.session.commit()

    def filter(self, *expressions: ColumnElement) -> list[Model]:
        """Filters entities based on given SQLAlchemy expressions.

        Args:
            *expressions (ColumnElement): SQLAlchemy filter expressions.

        Returns:
            list[Model]: A list of entity instances matching the criteria.
        """
        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        return list(self.session.execute(query).scalars())

    def filter_one_or_none(self, *expressions: ColumnElement) -> Optional[Model]:
        """Filters for one entity or none based on given SQLAlchemy expressions.

        Args:
            *expressions (ColumnElement): SQLAlchemy filter expressions.

        Returns:
            Optional[Model]: A single entity instance if found, otherwise None.
        """
        query = select(self.model)
        if expressions:
            query = query.where(*expressions)
        return self.session.execute(query).scalar_one_or_none()


class UserRepository(DatabaseRepository[models.UserEntity]):
    """Repository for UserEntity database operations."""
    def __init__(self, session: Session):
        """Initializes the user repository.

        Args:
            session (Session): The SQLAlchemy session.
        """
        super().__init__(models.UserEntity, session)

    def get_by_username(self, username: str) -> Optional[models.UserEntity]:
        """Retrieves a user by their username.

        Args:
            username (str): The username of the user.

        Returns:
            Optional[models.UserEntity]: The user entity if found, otherwise None.
        """
        return self.filter_one_or_none(models.UserEntity.username == username)

    def get_by_email(self, email: str) -> Optional[models.UserEntity]:
        """Retrieves a user by their email address.

        Args:
            email (str): The email address of the user.

        Returns:
            Optional[models.UserEntity]: The user entity if found, otherwise None.
        """
        return self.filter_one_or_none(models.UserEntity.email == email)


class FolderRepository(DatabaseRepository[models.FolderEntity]):
    """Repository for FolderEntity database operations."""
    def __init__(self, session: Session):
        """Initializes the folder repository.

        Args:
            session (Session): The SQLAlchemy session.
        """
        super().__init__(models.FolderEntity, session)

    def get_by_name_and_parent_id(
        self, name: str, parent_id: str | None
    ) -> Optional[models.FolderEntity]:
        """Retrieves a folder by its name and parent folder ID.

        Args:
            name (str): The name of the folder.
            parent_id (str | None): The ID of the parent folder, or None for root.

        Returns:
            Optional[models.FolderEntity]: The folder entity if found, otherwise None.
        """
        return self.filter_one_or_none(
            models.FolderEntity.parent_folder_id == parent_id,
            models.FolderEntity.name == name,
        )


class FileRepository(DatabaseRepository[models.FileEntity]):
    """Repository for FileEntity database operations."""
    def __init__(self, session: Session):
        """Initializes the file repository.

        Args:
            session (Session): The SQLAlchemy session.
        """
        super().__init__(models.FileEntity, session)

    def get_by_name_and_parent(
        self, name: str, parent: models.FolderEntity
    ) -> Optional[models.FileEntity]:
        """Retrieves a file by its name and parent folder.

        Args:
            name (str): The name of the file.
            parent (models.FolderEntity): The parent folder entity.

        Returns:
            Optional[models.FileEntity]: The file entity if found, otherwise None.
        """
        return self.filter_one_or_none(
            models.FileEntity.name == name, models.FileEntity.folder == parent
        )


class SharedFileRepository(DatabaseRepository[models.SharedFileEntity]):
    """Repository for SharedFileEntity database operations."""
    def __init__(self, session: Session):
        """Initializes the shared file repository.

        Args:
            session (Session): The SQLAlchemy session.
        """
        super().__init__(models.SharedFileEntity, session)

    def get_shared_files_by_file_id(self, file_id: str) -> list[models.SharedFileEntity]:
        """Retrieves all shared file entries for a given file ID.

        Args:
            file_id (str): The ID of the file.

        Returns:
            list[models.SharedFileEntity]: A list of shared file entities.
        """
        return self.filter(models.SharedFileEntity.file_id == file_id)

    def is_file_shared_to_user(self, file_id: str, user_id: str) -> bool:
        """Checks if a file is shared with a specific user.

        Args:
            file_id (str): The ID of the file.
            user_id (str): The ID of the user.

        Returns:
            bool: True if the file is shared with the user, False otherwise.
        """
        return (
            self.filter_one_or_none(
                models.SharedFileEntity.file_id == file_id,
                models.SharedFileEntity.user_id == user_id,
            )
            is not None
        )

    def delete_shared_files_from_users(self, file_id: str, user_id: str) -> None:
        """Deletes a specific shared file entry for a user.

        Args:
            file_id (str): The ID of the file.
            user_id (str): The ID of the user from whom the share is removed.
        """
        shared_file = self.filter_one_or_none(
            models.SharedFileEntity.file_id == file_id,
            models.SharedFileEntity.user_id == user_id,
        )
        if shared_file:
            self.delete(shared_file)


class LinkRepository(DatabaseRepository[models.LinkEntity]):
    """Repository for LinkEntity database operations."""
    def __init__(self, session: Session):
        """Initializes the link repository.

        Args:
            session (Session): The SQLAlchemy session.
        """
        super().__init__(models.LinkEntity, session)

    def get_by_name_and_parent(
        self, name: str, parent: models.FolderEntity
    ) -> Optional[models.LinkEntity]:
        """Retrieves a link by its name and parent folder.

        Args:
            name (str): The name of the link.
            parent (models.FolderEntity): The parent folder entity.

        Returns:
            Optional[models.LinkEntity]: The link entity if found, otherwise None.
        """
        return self.filter_one_or_none(
            models.LinkEntity.name == name, models.LinkEntity.folder == parent
        )

    def get_by_file_id_and_owner_id(
        self, file_id: str, owner_id: str
    ) -> Optional[models.LinkEntity]:
        """Retrieves a link by its target file ID and owner ID.

        Args:
            file_id (str): The ID of the target file.
            owner_id (str): The ID of the link owner.

        Returns:
            Optional[models.LinkEntity]: The link entity if found, otherwise None.
        """
        return self.filter_one_or_none(
            models.LinkEntity.target_file_id == file_id, models.LinkEntity.owner_id == owner_id
        )

    def get_by_file_id(self, file_id: str) -> list[models.LinkEntity]:
        """Retrieves all links pointing to a specific file ID.

        Args:
            file_id (str): The ID of the target file.

        Returns:
            list[models.LinkEntity]: A list of link entities.
        """
        return self.filter(models.LinkEntity.target_file_id == file_id)
