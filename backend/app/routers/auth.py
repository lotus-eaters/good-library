from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserOut
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = not settings.is_development
    response.set_cookie("access_token", access_token, httponly=True, secure=secure, samesite="lax",
                        max_age=settings.access_token_expire_minutes * 60)
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=secure, samesite="lax",
                        max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth/refresh")


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(body: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(
        db, email=body.email, username=body.username,
        password=body.password, display_name=body.display_name,
    )
    access_token, refresh_token = await auth_service.refresh(db, user_id=user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(message="Account created", user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user, access_token, refresh_token = await auth_service.login(db, email=body.email, password=body.password)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(message="Logged in", user=UserOut.model_validate(user))


@router.post("/logout")
async def logout(response: Response):
    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    access_token, refresh_token = await auth_service.refresh(db, user_id=user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(message="Tokens refreshed", user=UserOut.model_validate(user))
