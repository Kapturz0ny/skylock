import uuid
from typing import Optional, List
from sqlalchemy import orm, ForeignKey


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
    email: orm.Mapped[str] = orm.mapped_column(nullable=True)

    folders: orm.Mapped[List["FolderEntity"]] = orm.relationship(
        "FolderEntity", back_populates="owner", lazy="selectin"
    )
    files: orm.Mapped[List["FileEntity"]] = orm.relationship(
        "FileEntity", back_populates="owner", lazy="selectin"
    )


class FolderEntity(Base):
    __tablename__ = "folders"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    parent_folder_id: orm.Mapped[Optional[int]] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("users.id"))
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


class FileEntity(Base):
    __tablename__ = "files"

    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    folder_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("folders.id"))
    owner_id: orm.Mapped[int] = orm.mapped_column(ForeignKey("users.id"))
    is_public: orm.Mapped[bool] = orm.mapped_column(nullable=False, default=False)

    folder: orm.Mapped[FolderEntity] = orm.relationship("FolderEntity", back_populates="files")

    owner: orm.Mapped[UserEntity] = orm.relationship("UserEntity", back_populates="files")
