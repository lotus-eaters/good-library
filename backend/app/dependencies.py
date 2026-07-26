from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionFactory
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.utils.security import decode_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a database session for the duration of one request.
    Automatically rolls back on error, always closes when done.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def _extract_token(request: Request) -> str | None:
    """Read JWT from httpOnly cookie first, then Authorization header as fallback."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    return token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency for protected routes.
    Decodes the JWT, loads the user from DB, raises 401 if anything is wrong.
    Usage: user: User = Depends(get_current_user)
    """
    token = _extract_token(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = await user_repository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Dependency for public routes that behave differently when logged in.
    Returns the User if authenticated, None if not — never raises.
    Usage: user: User | None = Depends(get_optional_user)
    """
    token = _extract_token(request)
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        user = await user_repository.get_by_id(db, user_id)
        return user if (user and user.is_active) else None
    except (JWTError, KeyError, ValueError):
        return None
