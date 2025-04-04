from typing import Annotated
from fastapi import APIRouter, Depends, status

from skylock.api import models
from skylock.api.dependencies import get_skylock_facade
from skylock.skylock_facade import SkylockFacade

router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        """
    This endpoint allows a new user to register with a unique username and password.
    If the username already exists, a 409 Conflict error will be raised.
    """
    ),
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {"example": {"message": "User successfully registered"}}
            },
        },
        409: {
            "description": "User with the provided username already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "User with username {username} already exists"}
                }
            },
        },
    },
)
def register_user(
    request: models.RegisterUserRequest,
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
):
    skylock.register_user(username=request.username, password=request.password, email=request.email)
    return {"message": "User is not in the database"}


@router.post(
    "/2FA",
    status_code=status.HTTP_201_CREATED,
    summary="Verify 2FA",
    description=(
        """
    This endpoint allows a new user to verify email using 2FA.
    If the code has expired or the code is wrong, a 409 Conflict error will be raised.
    """
    ),
    response_model=None,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {"example": {"message": "User successfully registered"}}
            },
        },
        401: {
            "description": "2FA code is wrong",
            "content": {
                "application/json": {"example": {"detail": "2FA code is wrong/has expired"}}
            },
        },
    },
)
def register_user(
    request: models.FAWithCode,
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
) -> dict:
    skylock.verify_2FA(
        username=request.username, password=request.password, code=request.code, email=request.email
    )
    return {"message": "User successfully registered"}


@router.post(
    "/login",
    response_model=models.Token,
    summary="Authenticate user and get JWT token",
    description=(
        """
        "This endpoint allows an existing user to authenticate using their username and password.
        A JWT token is returned if the credentials are valid.
        """
    ),
    responses={
        200: {
            "description": "Successful login, JWT token returned",
            "content": {
                "application/json": {
                    "example": {"access_token": "{JWT_TOKEN}", "token_type": "bearer"}
                }
            },
        },
        401: {
            "description": "Invalid credentials provided",
            "content": {"application/json": {"example": {"detail": "Invalid credentials"}}},
        },
    },
)
def login_user(
    request: models.LoginUserRequest,
    skylock: Annotated[SkylockFacade, Depends(get_skylock_facade)],
) -> models.Token:
    return skylock.login_user(username=request.username, password=request.password)
