"""
Context model class.
"""

from typing import Optional, Annotated
from pydantic import BaseModel, Field
from skylock_cli.model.token import Token
from skylock_cli.model.directory import Directory


class Context(BaseModel):
    """Stores context information."""

    token: Annotated[Optional[Token], Field(description="Token object")] = None
    cwd: Annotated[
        Optional[Directory], Field(description="Current working directory")
    ] = None
    base_url: Annotated[str, Field(description="Base URL of the SkyLock server")] = (
        "http://localhost:8000"
    )
    username: Annotated[
        Optional[str], Field(description="Username of the logged-in user")
    ] = None
