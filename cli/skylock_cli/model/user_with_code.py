"""
User with 2FA code model class.
"""

from skylock_cli.model import user_with_email


class UserWithCode(user_with_email.UserWithEmail):
    """User (inhareting from User model class) but with 2FA code"""
    code: str
