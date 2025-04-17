import pytest
from unittest.mock import MagicMock

from skylock.pages.html_builder import HtmlBuilder
from skylock.skylock_facade import SkylockFacade
from fastapi.templating import Jinja2Templates
from skylock.utils.url_generator import UrlGenerator


@pytest.fixture
def mock_skylock_facade():
    mock = MagicMock(spec=SkylockFacade)
    mock._user_service = MagicMock()
    mock._user_service.user_repository = MagicMock()
    return mock


@pytest.fixture
def mock_url_generator():
    return MagicMock(spec=UrlGenerator)


@pytest.fixture
def mock_templates():
    return MagicMock(spec=Jinja2Templates)


@pytest.fixture
def html_builder(mock_skylock_facade, mock_templates, mock_url_generator):
    return HtmlBuilder(mock_skylock_facade, mock_templates, mock_url_generator)
