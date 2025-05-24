import uuid
import json
from typing import Optional, List
from sqlalchemy import orm, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from skylock.api.models import Privacy, FolderType


class Base(orm.DeclarativeBase):
    id: orm.Mapped[str] = orm.mapped_column(
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


metadata = Base.metadata


class UserEntity(Base):
    __tablename__ = "users"

    username: orm.Mapped[str] = orm.mapped_column(unique=True, nullable=False)
    password: orm.Mapped[str] = orm.mapped_column(nullable=False)
    email: orm.Mapped[str] = orm.mapped_column(unique=True, nullable=True)

    folders: orm.Mapped[List["FolderEntity"]] = orm.relationship(
        "FolderEntity", back_populates="owner", lazy="selectin"
    )
    files: orm.Mapped[List["FileEntity"]] = orm.relationship(
        "FileEntity", back_populates="owner", lazy="selectin"
    )
    shared_files: orm.Mapped[List["SharedFileEntity"]] = orm.relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )


class FolderEntity(Base):
    __tablename__ = "folders"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    parent_folder_id: orm.Mapped[Optional[str]] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"))
    privacy: orm.Mapped[str] = orm.mapped_column(nullable=False, default=Privacy.PRIVATE)

    parent_folder: orm.Mapped[Optional["FolderEntity"]] = orm.relationship(
        "FolderEntity", remote_side="FolderEntity.id", back_populates="subfolders"
    )

    files: orm.Mapped[List["FileEntity"]] = orm.relationship(
        "FileEntity", back_populates="folder", lazy="selectin"
    )

    subfolders: orm.Mapped[List["FolderEntity"]] = orm.relationship(
        "FolderEntity", back_populates="parent_folder", lazy="selectin"
    )

    links: orm.Mapped[List["LinkEntity"]] = orm.relationship(
        "LinkEntity",
        back_populates="folder",
        lazy="selectin",
        foreign_keys="LinkEntity.folder_id",
    )

    owner: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="folders")

    type: orm.Mapped[str] = orm.mapped_column(nullable=False, default=FolderType.NORMAL)

    def is_root(self) -> bool:
        return self.parent_folder_id is None


class FileEntity(Base):
    __tablename__ = "files"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    folder_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"))
    privacy: orm.Mapped[str] = orm.mapped_column(nullable=False, default=Privacy.PRIVATE)
    shared_to: orm.Mapped[List[str]] = orm.mapped_column(TEXT, default=set)
    size: orm.Mapped[int] = orm.mapped_column(nullable=False)

    folder: orm.Mapped[FolderEntity] = orm.relationship("FolderEntity", back_populates="files")
    owner: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="files")
    shared_with: orm.Mapped[List["SharedFileEntity"]] = orm.relationship(
        back_populates="file", lazy="selectin", cascade="all, delete-orphan"
    )

    def _set_shared_to(self, value: set[str]):
        self.__shared_to = json.dumps(list(value))

    def _get_shared_to(self) -> set[str]:
        if self.__shared_to:
            return set(json.loads(self.__shared_to))
        return set()

    __shared_to: orm.Mapped[Optional[str]] = orm.mapped_column(TEXT, default=None, name="shared_to")
    shared_to = property(_get_shared_to, _set_shared_to)


class SharedFileEntity(Base):
    __tablename__ = "shared_files"

    file_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("files.id"), primary_key=True)
    user_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"), primary_key=True)

    file: orm.Mapped[FileEntity] = orm.relationship("FileEntity", back_populates="shared_with")
    user: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="shared_files")


class LinkEntity(Base):
    __tablename__ = "links"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    folder_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("folders.id"), nullable=False)
    owner_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"), nullable=False)
    resource_type: orm.Mapped[str] = orm.mapped_column(nullable=False)
    target_file_id: orm.Mapped[Optional[str]] = orm.mapped_column(
        ForeignKey("files.id"), nullable=True
    )
    target_folder_id: orm.Mapped[Optional[str]] = orm.mapped_column(
        ForeignKey("folders.id"), nullable=True
    )

    target_file: orm.Mapped[Optional["FileEntity"]] = orm.relationship(
        foreign_keys=[target_file_id]
    )
    target_folder: orm.Mapped[Optional["FolderEntity"]] = orm.relationship(
        foreign_keys=[target_folder_id]
    )
    folder: orm.Mapped["FolderEntity"] = orm.relationship(
        "FolderEntity", back_populates="links", foreign_keys=[folder_id]
    )
    owner: orm.Mapped["UserEntity"] = orm.relationship()
