class UrlGenerator:
    def generate_url_for_file(self, file_id: str) -> str:
        return f"/files/{file_id}"

    def generate_url_for_folder(self, folder_id: str) -> str:
        return f"/folders/{folder_id}"

    def generate_download_url_for_file(self, file_id: str) -> str:
        return f"/api/v1/public/files/download/{file_id}"
    
    def generate_login_url_for_file(self, file_id: str) -> str:
        return f"/files/{file_id}/login"
