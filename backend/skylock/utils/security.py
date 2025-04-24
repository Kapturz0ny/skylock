from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from skylock.config import JWT_SECRET
from skylock.database import models as db_models
from skylock.database.repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_user_from_jwt(token: str, user_repository: UserRepository) -> db_models.UserEntity:
    try:
        user_data = decode_jwt(token)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e

    user_id = user_data.get("id")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


def create_jwt_for_user(user: db_models.UserEntity) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"id": user.id, "sub": user.username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
