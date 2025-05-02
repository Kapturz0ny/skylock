"""
User model class.
"""

from typing import Annotated
from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Stores user information.
    """

    username: Annotated[str, Field(description="Username of the user")]
    password: Annotated[str, Field(description="Password of the user")]
