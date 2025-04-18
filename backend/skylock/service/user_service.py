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
    def __init__(self, user_repository: UserRepository, redis_mem=None, logger=None):
        self.user_repository = user_repository
        self.password_hasher = argon2.PasswordHasher()

        self.logger = logger or s_logger
        self.redis_mem = redis_mem or s_redis_mem
        self.TOKEN_LIFE = 600

    def register_user(self, username: str, password: str, email: str) -> None:
        existing_user_entity = self.user_repository.get_by_username(username)
        existing_mail_entity = self.user_repository.get_by_email(email)

        if existing_user_entity or existing_mail_entity:
            raise UserAlreadyExists()
        user_secret = pyotp.random_base32()

        self.redis_mem.setex(f"2fa:{username}", self.TOKEN_LIFE + 5, user_secret)

        totp = pyotp.TOTP(user_secret, interval=self.TOKEN_LIFE)

        subject = "Complete you registration to Skylock!"
        body = two_fa_code_mail(username, totp.now(), self.TOKEN_LIFE)

        send_mail(email, subject, body)
        # TODO handle potential send_mail error
        if ENV_TYPE == "dev":
            self.logger.info(f"TOTP for user: {totp.now()}")

    def verify_2FA(
        self, username: str, password: str, code: str, email: str
    ) -> db_models.UserEntity:
        user_secret = self.redis_mem.get(f"2fa:{username}")
        if not user_secret:
            raise Wrong2FAException(message="Code has expired")

        totp = pyotp.TOTP(user_secret, interval=self.TOKEN_LIFE)
        if totp.verify(code):
            hashed_password = self.password_hasher.hash(password)
            new_user_entity = db_models.UserEntity(
                username=username, password=hashed_password, email=email
            )
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

    def find_shared_to_users(self, usernames: list[str]) -> list[str]:
        found_users = []
        for user in usernames:
            user_entity = self.user_repository.get_by_username(user)
            if user_entity:
                found_users.append(user_entity.username)
        return found_users
