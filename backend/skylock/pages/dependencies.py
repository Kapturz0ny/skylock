from typing import Annotated

from fastapi import Depends
from skylock.api.dependencies import get_skylock_facade, get_url_generator
from fastapi.templating import Jinja2Templates

from skylock.pages.html_builder import HtmlBuilder
from skylock.skylock_facade import SkylockFacade
from skylock.utils.url_generator import UrlGenerator


def get_templates() -> Jinja2Templates:
    """Creates and returns a Jinja2Templates instance.

    Returns:
        Jinja2Templates: An instance configured to load templates from the "templates" directory.
    """
    return Jinja2Templates("templates")


def get_html_builder(
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
    url_generator: Annotated[UrlGenerator, Depends(get_url_generator)],
) -> HtmlBuilder:
    """Creates and returns an HtmlBuilder instance.

    Args:
        skylock (SkylockFacade): The Skylock facade instance.
        templates (Jinja2Templates): The Jinja2 templates instance.
        url_generator (UrlGenerator): The URL generator instance.

    Returns:
        HtmlBuilder: An instance of HtmlBuilder initialized with the provided dependencies.
    """
    return HtmlBuilder(skylock=skylock, templates=templates, url_generator=url_generator)
