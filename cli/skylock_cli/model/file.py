"""
Module with File model class
"""

from pathlib import Path
from typing import Annotated, Optional
from pydantic import Field
from typer.colors import YELLOW
from skylock_cli.model.resource import Resource


class File(Resource):
    """Stores file metadata"""

    name: Annotated[str, Field(description="File name")]
    size: Annotated[int, Field(description="File size (in bytes)")]
    path: Annotated[Path, Field(description="File path")]
    color: Annotated[
        Optional[str], Field(description="File color used to pretty print in CLI")
    ] = YELLOW
    type_label: Annotated[str, Field(description="Type of resource")] = "file"
