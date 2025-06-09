class UrlGenerator:
    def generate_url_for_file(self, file_id: str) -> str:
        return f"/files/{file_id}"

    def generate_url_for_folder(self, folder_id: str) -> str:
        return f"/folders/{folder_id}"

    def generate_download_url_for_file(self, file_id: str) -> str:
        return f"/api/v1/shared/files/download/id/{file_id}"

    def generate_import_url_for_file(self, file_id: str) -> str:
        return f"/files/{file_id}/import"
