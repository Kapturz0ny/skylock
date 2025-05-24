from enum import Enum as PyEnum
from dataclasses import dataclass
from typing import IO
from pydantic import BaseModel


class Privacy(str, PyEnum):
    PRIVATE = "private"
    PROTECTED = "protected"
    PUBLIC = "public"


class FolderType(str, PyEnum):
    NORMAL = "normal"
    SHARED = "shared"
    SHARING_USER = "sharing_user"


class ResourceType(str, PyEnum):
    FILE = "file"
    FOLDER = "folder"
    LINK = "link"


class Token(BaseModel):
    access_token: str
    token_type: str


class Folder(BaseModel):
    id: str
    name: str
    path: str
    privacy: Privacy


class File(BaseModel):
    id: str
    name: str
    path: str
    owner_id: str
    privacy: Privacy
    size: int
    shared_to: list[str] = []


class Link(BaseModel):
    id: str
    name: str
    path: str


class FolderContents(BaseModel):
    folder_name: str
    folder_path: str
    files: list[File]
    folders: list[Folder]
    links: list[Link]


@dataclass
class FileData:
    name: str
    data: IO[bytes]


@dataclass
class FolderData:
    name: str
    data: IO[bytes]


class LoginUserRequest(BaseModel):
    username: str
    password: str


class RegisterUserRequest(BaseModel):
    username: str
    password: str
    email: str


class UpdateFolderRequest(BaseModel):
    privacy: Privacy
    recursive: bool = False


class UpdateFileRequest(BaseModel):
    privacy: Privacy
    shared: list[str] = []


class UploadOptions(BaseModel):
    force: bool
    privacy: Privacy


class ResourceLocationResponse(BaseModel):
    location: str


class FAWithCode(BaseModel):
    code: str
    username: str
    password: str
    email: str
