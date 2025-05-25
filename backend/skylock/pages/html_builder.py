from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from skylock.skylock_facade import SkylockFacade
from skylock.utils.url_generator import UrlGenerator

from skylock.utils.security import get_user_from_jwt
from skylock.api.models import Privacy


class HtmlBuilder:
    """Builds various HTML pages for the application."""

    def __init__(
        self,
        skylock: SkylockFacade,
        templates: Jinja2Templates,
        url_generator: UrlGenerator,
    ):
        """Initializes the HtmlBuilder.

        Args:
            skylock (SkylockFacade): The main application facade.
            templates (Jinja2Templates): Jinja2 templates engine.
            url_generator (UrlGenerator): Utility for generating URLs.
        """
        self._skylock = skylock
        self._templates = templates
        self._url_generator = url_generator

    def build_main_page(self, request: Request) -> HTMLResponse:
        """Builds the main index HTML page.

        Args:
            request (Request): The incoming HTTP request.

        Returns:
            HTMLResponse: The rendered main page.
        """
        return self._templates.TemplateResponse(request, "index.html")

    def build_folder_contents_page(self, request: Request, folder_id: str) -> HTMLResponse:
        """Builds the HTML page displaying the contents of a specific folder.

        Only public files and folders within the specified folder are listed.

        Args:
            request (Request): The incoming HTTP request.
            folder_id (str): The ID of the folder whose contents are to be displayed.

        Returns:
            HTMLResponse: The rendered folder contents page.
        """
        folder_contents = self._skylock.get_public_folder_contents(folder_id)
        public_folders = [
            {
                "name": folder.name,
                "url": self._url_generator.generate_url_for_folder(folder.id),
            }
            for folder in folder_contents.folders
            if folder.privacy == Privacy.PUBLIC
        ]
        public_files = [
            {
                "name": file.name,
                "url": self._url_generator.generate_url_for_file(file.id),
            }
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
        """Builds the HTML page for a specific file, handling access control.

        It checks file privacy (public, protected, private) and user authentication
        to determine if the user can view the file details or needs to log in.

        Args:
            request (Request): The incoming HTTP request.
            file_id (str): The ID of the file to display.

        Returns:
            HTMLResponse: The rendered file page or a login page if access is restricted.
        """
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
                {
                    "file": {
                        "name": file.name,
                        "path": file.path,
                        "download_url": download_url,
                        "import_url": import_url,
                    }
                },
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
            {
                "file": {
                    "name": file.name,
                    "path": file.path,
                    "download_url": download_url,
                }
            },
        )

    def build_login_page(self, request: Request, file_id: str, error: str = "") -> HTMLResponse:
        """Builds the HTML login page.

        This page is typically shown when a user tries to access a protected or
        private file without being authenticated or authorized.

        Args:
            request (Request): The incoming HTTP request.
            file_id (str): The ID of the file the user was trying to access.
            error (str, optional): An error message to display on the login page.
                                   Defaults to an empty string.

        Returns:
            HTMLResponse: The rendered login page.
        """
        return self._templates.TemplateResponse(
            request,
            "login_form.html",
            {"file_id": file_id, "error": error},
        )
    