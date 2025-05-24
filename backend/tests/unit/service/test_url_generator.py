import pytest
from skylock.utils.url_generator import UrlGenerator


@pytest.fixture
def url_generator():
    return UrlGenerator()


def test_generate_url_for_file(url_generator):
    file_id = "12345"
    expected_url = "/files/12345"
    assert url_generator.generate_url_for_file(file_id) == expected_url


def test_generate_url_for_folder(url_generator):
    folder_id = "67890"
    expected_url = "/folders/67890"
    assert url_generator.generate_url_for_folder(folder_id) == expected_url


def test_generate_download_url_for_file(url_generator):
    file_id = "abcde"
    expected_url = "/api/v1/shared/files/download/abcde"
    assert url_generator.generate_download_url_for_file(file_id) == expected_url
