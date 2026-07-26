from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import user_repository
from app.services.shelf_service import shelf_service
from app.utils.security import create_access_token, create_refresh_token


class OAuthService:
    async def get_or_create_google_user(
        self,
        db: AsyncSession,
        *,
        google_id: str,
        email: str,
        name: str,
        avatar_url: str | None,
    ) -> tuple[User, bool]:
        """
        Find existing user by google_id or email, or create a new one.
        Returns (user, is_new_user).
        """
        # 1. Existing OAuth user
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(
                User.oauth_provider == "google",
                User.oauth_provider_id == google_id,
            )
        )
        user = result.scalar_one_or_none()
        if user:
            return user, False

        # 2. Existing email/password user → link their Google account
        user = await user_repository.get_by_email(db, email)
        if user:
            user.oauth_provider = "google"
            user.oauth_provider_id = google_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            await db.flush()
            await db.commit()
            return user, False

        # 3. Brand new user via Google OAuth
        username = await self._generate_username(db, email)
        user = User(
            email=email.lower(),
            username=username,
            hashed_password=None,
            display_name=name,
            avatar_url=avatar_url,
            oauth_provider="google",
            oauth_provider_id=google_id,
            is_verified=True,  # Google has already verified the email
        )
        user = await user_repository.create(db, user)
        await shelf_service.create_default_shelves(db, user.id)
        await db.commit()
        await db.refresh(user)
        return user, True

    def issue_tokens(self, user_id: int) -> tuple[str, str]:
        return create_access_token(user_id), create_refresh_token(user_id)

    async def _generate_username(self, db: AsyncSession, email: str) -> str:
        """Derive a unique username from the email address."""
        base = email.split("@")[0].lower().replace(".", "_").replace("-", "_")[:30]
        username = base
        counter = 1
        while await user_repository.username_exists(db, username):
            username = f"{base}{counter}"
            counter += 1
        return username


oauth_service = OAuthService()
