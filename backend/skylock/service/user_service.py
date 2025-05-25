import argon2
import pyotp

from skylock.api import models
from skylock.database.repository import UserRepository
from skylock.database import models as db_models
from skylock.utils.security import create_jwt_for_user
from skylock.utils.exceptions import (
    UserAlreadyExists,
    InvalidCredentialsException,
    Wrong2FAException,
)
from skylock.config import ENV_TYPE
from skylock.service.gmail import send_mail
from skylock.utils.logger import logger as s_logger
from skylock.utils.reddis_mem import redis_mem as s_redis_mem
from templates.mails import two_fa_code_mail


class UserService:
    """Manages user-related operations like registration, login, and 2FA."""

    def __init__(self, user_repository: UserRepository, redis_mem=None, logger=None):
        """Initializes the UserService.

        Args:
            user_repository: Repository for user data access.
            redis_mem: Optional Redis client for storing 2FA secrets.
            logger: Optional logger instance.
        """
        self.user_repository = user_repository
        self.password_hasher = argon2.PasswordHasher()

        self.logger = logger or s_logger
        self.redis_mem = redis_mem or s_redis_mem
        self.token_life = 600

    def register_user(self, username: str, email: str) -> None:
        """Initiates user registration by sending a 2FA code to the user's email.

        It checks if the username or email already exists. If not, it generates
        a 2FA secret, stores it temporarily, and emails a TOTP code to the user.

        Args:
            username: The desired username for the new user.
            email: The email address for the new user.

        Raises:
            UserAlreadyExists: If the username or email is already in use.
            Exception: If sending the email fails.
        """
        existing_user_entity = self.user_repository.get_by_username(username)
        existing_mail_entity = self.user_repository.get_by_email(email)

        if existing_user_entity or existing_mail_entity:
            raise UserAlreadyExists()
        user_secret = pyotp.random_base32()

        self.redis_mem.setex(f"2fa:{username}", self.token_life + 5, user_secret)

        totp = pyotp.TOTP(user_secret, interval=self.token_life)

        subject = "Complete you registration to Skylock!"
        body = two_fa_code_mail(username, totp.now(), self.token_life)

        try:
            send_mail(email, subject, body)
        except Exception as e:
            raise e

        if ENV_TYPE == "dev":
            self.logger.info(f"TOTP for user: {totp.now()}")

    def verify_2fa(
        self, username: str, password: str, code: str, email: str
    ) -> db_models.UserEntity:
        """Verifies the 2FA code and completes user registration.

        It retrieves the 2FA secret, verifies the provided code, hashes the password,
        and saves the new user to the database.

        Args:
            username: The username of the user being verified.
            password: The user's chosen plain-text password.
            code: The 2FA code submitted by the user.
            email: The user's email address (used for creating the user entity).

        Returns:
            The created `db_models.UserEntity` object upon successful verification and saving.

        Raises:
            Wrong2FAException: If the 2FA code is invalid, expired, or the secret is not found.
        """
        user_secret = self.redis_mem.get(f"2fa:{username}")
        if not user_secret:
            raise Wrong2FAException(message="Code has expired or secret not found")

        totp = pyotp.TOTP(str(user_secret), interval=self.token_life)
        if totp.verify(code):
            hashed_password = self.password_hasher.hash(password)
            new_user_entity = db_models.UserEntity(
                username=username, password=hashed_password, email=email
            )
            return self.user_repository.save(new_user_entity)

        raise Wrong2FAException(message="Invalid 2FA code")

    def login_user(self, username: str, password: str) -> models.Token:
        """Authenticates a user with their username and password.

        It retrieves the user by username, verifies the password, and if successful,
        generates and returns a JWT.

        Args:
            username: The username of the user attempting to log in.
            password: The plain-text password provided by the user.

        Returns:
            A `models.Token` object containing the access token and token type.

        Raises:
            InvalidCredentialsException: If the username is not found or the password
                                         does not match.
        """
        user_entity = self.user_repository.get_by_username(username)
        if user_entity and self._verify_password(user_entity.password, password):
            token = create_jwt_for_user(user_entity)
            return models.Token(access_token=token, token_type="bearer")
        raise InvalidCredentialsException

    def _verify_password(self, hashed_password: str, password: str) -> bool:
        """Verifies a plain-text password against a stored hashed password.

        Args:
            hashed_password: The stored Argon2 hashed password.
            password: The plain-text password to verify.

        Returns:
            True if the password matches the hash, False otherwise.
        """
        try:
            self.password_hasher.verify(hashed_password, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False

    def find_shared_to_users(self, usernames: list[str]) -> list[str]:
        """Filters a list of usernames, returning only those that exist in the system.

        Args:
            usernames: A list of usernames to check for existence.

        Returns:
            A list containing only the usernames that correspond to actual users.
        """
        found_users = []
        for user in usernames:
            user_entity = self.user_repository.get_by_username(user)
            if user_entity:
                found_users.append(user_entity.username)
        return found_users
