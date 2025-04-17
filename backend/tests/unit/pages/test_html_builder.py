from skylock.api.models import File, Privacy


def test_build_file_page_public_file(html_builder):
    file = File(
        id="file_id",
        name="file_name",
        path="file_path",
        privacy=Privacy.PUBLIC,
        shared_to=[],
        owner_id="owner_id",
    )
    download_url = "http://example.com/download"

    html_builder._skylock.get_file_for_login.return_value = file
    html_builder._url_generator.generate_download_url_for_file.return_value = download_url
    html_builder._templates.TemplateResponse.return_value = (
        None,
        "file.html",
        {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
    )

    assert html_builder.build_file_page(None, "file_id") == (
        None,
        "file.html",
        {"file": {"name": file.name, "path": file.path, "download_url": download_url}},
    )
