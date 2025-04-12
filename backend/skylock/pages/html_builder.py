from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from skylock.skylock_facade import SkylockFacade
from skylock.utils.url_generator import UrlGenerator


class HtmlBuilder:
    def __init__(
        self, skylock: SkylockFacade, templates: Jinja2Templates, url_generator: UrlGenerator
    ):
        self._skylock = skylock
        self._templates = templates
        self._url_generator = url_generator

    def build_main_page(self, request: Request) -> HTMLResponse:
        return self._templates.TemplateResponse(request, "index.html")

    def build_folder_contents_page(self, request: Request, folder_id: str) -> HTMLResponse:
        folder_contents = self._skylock.get_public_folder_contents(folder_id)
        public_folders = [
            {"name": folder.name, "url": self._url_generator.generate_url_for_folder(folder.id)}
            for folder in folder_contents.folders
            if folder.is_public
        ]
        public_files = [
            {"name": file.name, "url": self._url_generator.generate_url_for_file(file.id)}
            for file in folder_contents.files
            if file.is_public
        ]
        return self._templates.TemplateResponse(
            request,
            "folder_contents.html",
            {
                "name": folder_contents.folder_name,
                "path": folder_contents.folder_path,
                "folders": public_folders,
                "files": public_files,
            },
        )

    def build_file_page(self, request: Request, file_id: str) -> HTMLResponse:
        file = self._skylock.get_public_file(file_id)
        download_url = self._url_generator.generate_download_url_for_file(file_id)
        return self._templates.TemplateResponse(
            request,
            "file.html",
            {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
        )

    def build_login_page(self, request: Request, file_id: str) -> HTMLResponse:
        file = self._skylock.get_file_for_login(file_id)
        return self._templates.TemplateResponse(
            request,
            "login.html",
            {"file_id": file_id, "name": file.name, "path": file.path},
        )