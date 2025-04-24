from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from skylock.skylock_facade import SkylockFacade
from skylock.utils.url_generator import UrlGenerator
from skylock.service.resource_service import ResourceService

from skylock.utils.security import get_user_from_jwt
from skylock.api.models import Privacy


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
            if folder.privacy == Privacy.PUBLIC
        ]
        public_files = [
            {"name": file.name, "url": self._url_generator.generate_url_for_file(file.id)}
            for file in folder_contents.files
            if file.privacy == Privacy.PUBLIC
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
        file = self._skylock.get_file_for_login(file_id)
        download_url = self._url_generator.generate_download_url_for_file(file_id)
        privacy = file.privacy

        import_file_id = request.cookies.get("import_file")
        is_import = import_file_id == file_id
        
        if privacy == Privacy.PUBLIC and not is_import:
            import_url = self._url_generator.generate_import_url_for_file(file_id)
            return self._templates.TemplateResponse(
                request,
                "file.html",
                {"file": {"name": file.name, "path": file.path, "download_url": download_url, "import_url": import_url}},
            )

        token = request.cookies.get("access_token")

        if token:
            token = token.replace("Bearer ", "")
        else:
            return self.build_login_page(request, file_id)
        try:
            user = get_user_from_jwt(token, self._skylock._user_service.user_repository)
        except HTTPException:
            return self.build_login_page(request, file_id, "Invalid Token")

        if (
            privacy == Privacy.PROTECTED
            and user.username not in file.shared_to
            and user.id != file.owner_id
        ):
            return self.build_login_page(request, file_id, "File not shared with you")

        if privacy == Privacy.PRIVATE and user.id != file.owner_id:
            return self.build_login_page(request, file_id, "File not shared with you")
        
        if privacy != Privacy.PRIVATE:
            self._skylock._resource_service.potential_file_import(user.id, file_id)

        return self._templates.TemplateResponse(
            request,
            "file.html",
            {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
        )

    def build_login_page(self, request: Request, file_id: str, error="") -> HTMLResponse:
        return self._templates.TemplateResponse(
            request,
            "login_form.html",
            {"file_id": file_id, "error": error},
        )
