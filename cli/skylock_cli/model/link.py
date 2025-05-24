"""
Module with Link model class
"""

from pathlib import Path
from typing import Annotated, Optional
from pydantic import Field
from typer.colors import GREEN
from skylock_cli.model.resource import Resource


class Link(Resource):
    """Symbolic Link to a resource: file, folder"""

    name: Annotated[str, Field(description="Link name")]
    path: Annotated[Path, Field(description="Link path")]
    color: Annotated[
        Optional[str], Field(description="Link color used to pretty print in CLI")
    ] = GREEN
    type_label: Annotated[str, Field(description="Type of resource")] = "link"
