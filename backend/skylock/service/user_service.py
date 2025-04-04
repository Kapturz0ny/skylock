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
from skylock.utils.logger import logger
from skylock.utils.reddis_mem import redis_mem
from skylock.config import ENV_TYPE
from skylock.service.gmail import send_mail


class UserService:
    def __init__(self, user_repository: UserRepository) -> str:
        self.user_repository = user_repository
        self.password_hasher = argon2.PasswordHasher()

        self.logger = logger
        self.redis_mem = redis_mem

    def register_user(self, username: str, password: str, email: str) -> None:
        existing_user_entity = self.user_repository.get_by_username(username)
        if existing_user_entity:
            raise UserAlreadyExists(f"User with username {username} already exists")
        # generate user_secret code
        user_secret = pyotp.random_base32()
        # cache user_secret
        self.redis_mem.setex(f"2fa:{username}", 300, user_secret)
        # generate OTP code
        totp = pyotp.TOTP(user_secret)
        # send OTP code using email
        subject = "Complete you registration to skylock!"
        body = "Enter your 2FA token to complete your registration process.\n" + \
            f"Your 2FA token: {totp}"
        send_mail(email, subject, body)
        # TODO handle potential send_mail error
        if ENV_TYPE == "dev":
            self.logger.info(f"TOTP for user: {totp.now()}")

    def verify_2FA(self, username: str, password: str, code: str) -> db_models.UserEntity:
        user_secret = self.redis_mem.get(f"2fa:{username}")
        if not user_secret:
            raise Wrong2FAException(message="Code has expired")

        totp = pyotp.TOTP(user_secret)
        if totp.verify(code):
            hashed_password = self.password_hasher.hash(password)
            new_user_entity = db_models.UserEntity(username=username, password=hashed_password)
            return self.user_repository.save(new_user_entity)

        raise Wrong2FAException

    def login_user(self, username: str, password: str) -> models.Token:
        user_entity = self.user_repository.get_by_username(username)
        if user_entity and self._verify_password(user_entity.password, password):
            token = create_jwt_for_user(user_entity)
            return models.Token(access_token=token, token_type="bearer")
        raise InvalidCredentialsException

    def verify_user(self, username: str, password: str) -> bool:
        user_entity = self.user_repository.get_by_username(username)
        if user_entity and self._verify_password(user_entity.password, password):
            return True
        return False

    def _verify_password(self, hashed_password, password) -> bool:
        try:
            self.password_hasher.verify(hashed_password, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
