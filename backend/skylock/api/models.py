from dataclasses import dataclass
from typing import IO, Literal
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class Folder(BaseModel):
    id: str
    name: str
    path: str
    is_public: bool


class File(BaseModel):
    id: str
    name: str
    path: str
    privacy: Literal["private", "protected", "public"]
    shared_to: list[str] = []


class FolderContents(BaseModel):
    folder_name: str
    folder_path: str
    files: list[File]
    folders: list[Folder]


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
    is_public: bool
    recursive: bool = False


class UpdateFileRequest(BaseModel):
    privacy: Literal["private", "protected", "public"]
    shared: list[str] = []


class UploadOptions(BaseModel):
    force: bool
    public: bool


class ResourceLocationResponse(BaseModel):
    location: str


class FAWithCode(BaseModel):
    code: str
    username: str
    password: str
    email: str
