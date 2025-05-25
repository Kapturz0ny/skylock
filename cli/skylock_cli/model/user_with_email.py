"""
User with email model class.
"""

from skylock_cli.model import user


class UserWithEmail(user.User):
    """User (inhareting from User model class) but with email"""
    email: str
