import hashlib
import hmac
import secrets

from app.core.config import get_settings

settings = get_settings()

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def generate_csrf_token() -> str:
    nonce = secrets.token_urlsafe(24)
    signature = hmac.new(
        settings.csrf_secret_key.encode(), nonce.encode(), hashlib.sha256
    ).hexdigest()
    return f"{nonce}.{signature}"


def is_valid_csrf_token(token: str) -> bool:
    try:
        nonce, signature = token.split(".", 1)
    except ValueError:
        return False
    expected = hmac.new(
        settings.csrf_secret_key.encode(), nonce.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def csrf_tokens_match(cookie_token: str | None, header_token: str | None) -> bool:
    if not cookie_token or not header_token:
        return False
    if not hmac.compare_digest(cookie_token, header_token):
        return False
    return is_valid_csrf_token(cookie_token)
