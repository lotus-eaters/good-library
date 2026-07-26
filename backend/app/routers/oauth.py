from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.services.oauth_service import oauth_service

router = APIRouter(prefix="/auth", tags=["oauth"])

_oauth = OAuth()
_oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google")
async def google_login(request: Request):
    """Redirect the user to Google's OAuth consent page."""
    return await _oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Google redirects here after the user approves.
    Exchange code → tokens → user info → find/create user → set JWT cookies → redirect to frontend.
    """
    token = await _oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo") or {}

    google_id = user_info.get("sub")
    email = user_info.get("email")

    if not google_id or not email:
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=oauth_failed")

    user, _ = await oauth_service.get_or_create_google_user(
        db,
        google_id=google_id,
        email=email,
        name=user_info.get("name", email.split("@")[0]),
        avatar_url=user_info.get("picture"),
    )

    access_token, refresh_token = oauth_service.issue_tokens(user.id)
    secure = not settings.is_development

    redirect = RedirectResponse(url=f"{settings.frontend_url}/")
    redirect.set_cookie("access_token", access_token, httponly=True, secure=secure, samesite="lax",
                        max_age=settings.access_token_expire_minutes * 60)
    redirect.set_cookie("refresh_token", refresh_token, httponly=True, secure=secure, samesite="lax",
                        max_age=settings.refresh_token_expire_days * 86400, path="/api/v1/auth/refresh")
    return redirect
