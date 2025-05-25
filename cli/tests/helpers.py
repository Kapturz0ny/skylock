"""Helper functions for tests."""

from unittest.mock import Mock
from http import HTTPStatus

from skylock_cli.model.token import Token
from skylock_cli.config import ROOT_PATH, LOCAL_HOST


def mock_response_with_status(status_code, json_data=None):
    """Create a mock response object with a status code."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    return mock_response


def assert_connect_error(result):
    """Connection error assert"""
    assert result.exit_code == 1
    assert (
        "The server is not reachable at the moment. Please try again later."
        in result.output
    )


def mock_test_context(path=ROOT_PATH, base_url=LOCAL_HOST):
    """Mock the test context with customized validity and expiration settings."""
    return Mock(
        token=Token(access_token="test_token", token_type="bearer"),
        cwd=Mock(path=path, name="/"),
        base_url=base_url,
    )


def mock_change_file_privacy(expected_privacy):
    def mock_side_effect(*args, **kwargs):
        passed_json = kwargs.get("json", {})

        return_json = {
            "name": "file.txt",
            "path": "/file.txt",
            "privacy": passed_json.get("privacy", expected_privacy),
            "size": 10,
        }

        return mock_response_with_status(HTTPStatus.OK, return_json)
    return mock_side_effect