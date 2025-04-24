from typing import Annotated

from fastapi import Depends
from skylock.api.dependencies import get_skylock_facade, get_url_generator
from fastapi.templating import Jinja2Templates

from skylock.pages.html_builder import HtmlBuilder
from skylock.skylock_facade import SkylockFacade
from skylock.utils.url_generator import UrlGenerator


def get_templates() -> Jinja2Templates:
    return Jinja2Templates("templates")


def get_html_bulder(
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    url_generator: Annotated[UrlGenerator, Depends(get_url_generator)],
) -> HtmlBuilder:
    return HtmlBuilder(skylock=skylock, templates=templates, url_generator=url_generator)
