from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import user_repository
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    async def register(
        self,
        db: AsyncSession,
        *,
        email: str,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        email = email.lower().strip()
        username = username.lower().strip()

        if await user_repository.email_exists(db, email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if await user_repository.username_exists(db, username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            display_name=display_name or username,
        )
        user = await user_repository.create(db, user)

        # Factory Pattern — create the 3 default shelves for every new user
        from app.services.shelf_service import shelf_service
        await shelf_service.create_default_shelves(db, user.id)

        await db.commit()
        await db.refresh(user)
        return user

    async def login(
        self,
        db: AsyncSession,
        *,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        """Returns (user, access_token, refresh_token)."""
        user = await user_repository.get_by_email(db, email.lower().strip())

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

        return user, create_access_token(user.id), create_refresh_token(user.id)

    async def refresh(self, db: AsyncSession, *, user_id: int) -> tuple[str, str]:
        """Issue a fresh token pair for a validated user."""
        user = await user_repository.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return create_access_token(user.id), create_refresh_token(user.id)


auth_service = AuthService()
