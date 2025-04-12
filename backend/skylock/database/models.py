import uuid
from typing import Optional, List, Set
from sqlalchemy import orm, ForeignKey, Enum, Table, Column, Text
from sqlalchemy.dialects.sqlite import TEXT  # Use TEXT from sqlite dialect
import json

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
    shared_files: orm.Mapped[List["FileEntity"]] = orm.relationship(
        secondary="shared_files", back_populates="shared_with"
    )

class FolderEntity(Base):
    __tablename__ = "folders"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    parent_folder_id: orm.Mapped[Optional[str]] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"))
    is_public: orm.Mapped[bool] = orm.mapped_column(nullable=False, default=False)

    parent_folder: orm.Mapped[Optional["FolderEntity"]] = orm.relationship(
        "FolderEntity", remote_side="FolderEntity.id", back_populates="subfolders"
    )

    files: orm.Mapped[List["FileEntity"]] = orm.relationship(
        "FileEntity", back_populates="folder", lazy="selectin"
    )

    subfolders: orm.Mapped[List["FolderEntity"]] = orm.relationship(
        "FolderEntity", back_populates="parent_folder", lazy="selectin"
    )

    owner: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="folders")

    def is_root(self) -> bool:
        return self.parent_folder_id is None

shared_files = Table(
    "shared_files",
    Base.metadata,
    Column("file_id", ForeignKey("files.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)

class FileEntity(Base):
    __tablename__ = "files"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    folder_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[str] = orm.mapped_column(ForeignKey("users.id"))
    privacy: orm.Mapped[str] = orm.mapped_column(Enum("private", "protected", "public"))
    shared_to: orm.Mapped[List[str]] = orm.mapped_column(TEXT, default=set)

    folder: orm.Mapped[FolderEntity] = orm.relationship("FolderEntity", back_populates="files")
    owner: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="files")
    shared_with: orm.Mapped[List["UserEntity"]] = orm.relationship(
        secondary=shared_files, back_populates="shared_files"
    )

    def _set_shared_to(self, value: list[str]):
        self.__shared_to = json.dumps(value)

    def _get_shared_to(self) -> list[str]:
        if self.__shared_to:
            return set(json.loads(self.__shared_to))
        return set()

    __shared_to: orm.Mapped[Optional[str]] = orm.mapped_column(TEXT, default=None, name="shared_to")
    shared_to = property(_get_shared_to, _set_shared_to)