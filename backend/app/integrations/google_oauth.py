import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings

settings = get_settings()

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class GoogleOAuthNotConfigured(Exception):
    pass


class GoogleOAuthError(Exception):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str
    email_verified: bool
    name: str
    picture: str | None


def is_configured() -> bool:
    return bool(
        settings.google_oauth_client_id
        and settings.google_oauth_client_secret
        and settings.google_oauth_redirect_uri
    )


def build_authorization_url(*, state: str, nonce: str, code_challenge: str) -> str:
    if not is_configured():
        raise GoogleOAuthNotConfigured("ورود با گوگل در حال حاضر پیکربندی نشده است.")

    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def generate_pkce_pair() -> tuple[str, str]:
    import base64
    import hashlib

    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


async def exchange_code(*, code: str, code_verifier: str) -> str:
    """Exchange the authorization code for tokens and return the raw ID token."""
    if not is_configured():
        raise GoogleOAuthNotConfigured("ورود با گوگل در حال حاضر پیکربندی نشده است.")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            TOKEN_ENDPOINT,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_oauth_redirect_uri,
            },
        )
    if response.status_code != 200:
        raise GoogleOAuthError("دریافت اطلاعات از گوگل ناموفق بود.")

    payload = response.json()
    raw_id_token = payload.get("id_token")
    if not raw_id_token:
        raise GoogleOAuthError("پاسخ گوگل فاقد شناسه معتبر است.")
    return str(raw_id_token)


def _verify_sync(raw_id_token: str, *, expected_nonce: str) -> GoogleIdentity:
    claims = google_id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
        raw_id_token, GoogleAuthRequest(), settings.google_oauth_client_id
    )

    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleOAuthError("صادرکننده توکن گوگل نامعتبر است.")
    if claims.get("nonce") != expected_nonce:
        raise GoogleOAuthError("اعتبارسنجی درخواست ورود با گوگل ناموفق بود.")
    if not claims.get("email"):
        raise GoogleOAuthError("گوگل ایمیل معتبری برنگرداند.")

    return GoogleIdentity(
        subject=claims["sub"],
        email=claims["email"],
        email_verified=bool(claims.get("email_verified", False)),
        name=claims.get("name", ""),
        picture=claims.get("picture"),
    )


async def verify_id_token(raw_id_token: str, *, expected_nonce: str) -> GoogleIdentity:
    return await run_in_threadpool(_verify_sync, raw_id_token, expected_nonce=expected_nonce)
