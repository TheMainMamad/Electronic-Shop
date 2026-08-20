import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.config import get_settings
from app.integrations.google_oauth import GoogleIdentity
from app.modules.auth.repository import (
    EmailVerificationRepository,
    PasswordResetRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.modules.auth.schemas import RegisterRequest
from app.modules.notifications.service import (
    send_email_verification_email,
    send_password_reset_email,
)
from app.modules.users.models import (
    EmailVerificationToken,
    OAuthAccount,
    OAuthProvider,
    PasswordResetToken,
    RefreshToken,
    User,
    UserRole,
)
from app.security.jwt import create_access_token
from app.security.password import hash_password, verify_password
from app.security.tokens import generate_opaque_token, hash_token

settings = get_settings()

GENERIC_LOGIN_ERROR = "ایمیل یا رمز عبور نادرست است."
PASSWORD_RESET_TTL = timedelta(hours=1)
EMAIL_VERIFICATION_TTL = timedelta(hours=48)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.password_resets = PasswordResetRepository(session)
        self.email_verifications = EmailVerificationRepository(session)

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_by_email(data.email):
            raise ConflictError("این ایمیل قبلاً ثبت‌نام کرده است.")
        if await self.users.get_by_username(data.username):
            raise ConflictError("این نام کاربری قبلاً استفاده شده است.")

        user = User(
            email=data.email.lower(),
            username=data.username,
            hashed_password=hash_password(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            role=UserRole.customer,
        )
        self.users.add(user)
        await self.session.flush()
        await self._issue_email_verification(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None or user.hashed_password is None:
            raise UnauthorizedError(GENERIC_LOGIN_ERROR)
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError(GENERIC_LOGIN_ERROR)
        if not user.is_active:
            raise UnauthorizedError("حساب کاربری شما غیرفعال شده است.")

        user.last_login = datetime.now(UTC)
        return user

    async def issue_token_pair(
        self, user: User, *, user_agent: str | None, ip_address: str | None
    ) -> tuple[str, str]:
        family_id = uuid.uuid4()
        access_token, raw_token, _ = await self._issue_refresh_token(
            user, family_id=family_id, user_agent=user_agent, ip_address=ip_address
        )
        return access_token, raw_token

    async def _issue_refresh_token(
        self,
        user: User,
        *,
        family_id: uuid.UUID,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[str, str, RefreshToken]:
        raw_token = generate_opaque_token()
        now = datetime.now(UTC)
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            family_id=family_id,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            created_at=now,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
        )
        self.refresh_tokens.add(refresh_token)
        await self.session.flush()

        access_token = create_access_token(user_id=user.id, role=user.role)
        return access_token, raw_token, refresh_token

    async def rotate_refresh_token(
        self, raw_refresh_token: str, *, user_agent: str | None, ip_address: str | None
    ) -> tuple[str, str, User]:
        token_hash = hash_token(raw_refresh_token)
        stored = await self.refresh_tokens.get_by_hash(token_hash)
        now = datetime.now(UTC)

        if stored is None:
            raise UnauthorizedError("نشست شما نامعتبر است. دوباره وارد شوید.")

        if stored.revoked_at is not None:
            # Reuse of an already-rotated/revoked token: treat as a breach and
            # kill the whole family so a stolen token can't be replayed. This
            # must be committed here — the route never reaches its own
            # commit() once this raises, so the revocation would otherwise be
            # silently rolled back and the "breach" would go unpunished.
            await self.refresh_tokens.revoke_family(stored.family_id, revoked_at=now)
            await self.session.commit()
            raise UnauthorizedError("نشست شما نامعتبر است. دوباره وارد شوید.")

        if stored.expires_at < now:
            raise UnauthorizedError("نشست شما منقضی شده است. دوباره وارد شوید.")

        user = await self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("نشست شما نامعتبر است. دوباره وارد شوید.")

        stored.revoked_at = now
        access_token, new_raw_token, new_token_row = await self._issue_refresh_token(
            user, family_id=stored.family_id, user_agent=user_agent, ip_address=ip_address
        )
        stored.replaced_by_id = new_token_row.id

        return access_token, new_raw_token, user

    async def logout(self, raw_refresh_token: str) -> None:
        stored = await self.refresh_tokens.get_by_hash(hash_token(raw_refresh_token))
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if user.hashed_password is None or not verify_password(
            current_password, user.hashed_password
        ):
            raise UnauthorizedError("رمز عبور فعلی نادرست است.")
        user.hashed_password = hash_password(new_password)
        await self.refresh_tokens.revoke_all_for_user(user.id, revoked_at=datetime.now(UTC))

    async def request_password_reset(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user is None:
            # Do not reveal whether the email exists.
            return
        raw_token = generate_opaque_token()
        self.password_resets.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.now(UTC) + PASSWORD_RESET_TTL,
                created_at=datetime.now(UTC),
            )
        )
        send_password_reset_email(to_email=user.email, token=raw_token)

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        record = await self.password_resets.get_by_hash(hash_token(token))
        if record is None or record.used_at is not None or record.expires_at < datetime.now(UTC):
            raise UnauthorizedError("لینک بازیابی رمز عبور نامعتبر یا منقضی‌شده است.")

        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise NotFoundError("کاربر پیدا نشد.")

        user.hashed_password = hash_password(new_password)
        record.used_at = datetime.now(UTC)
        await self.refresh_tokens.revoke_all_for_user(user.id, revoked_at=datetime.now(UTC))

    async def _issue_email_verification(self, user: User) -> None:
        raw_token = generate_opaque_token()
        self.email_verifications.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.now(UTC) + EMAIL_VERIFICATION_TTL,
                created_at=datetime.now(UTC),
            )
        )
        send_email_verification_email(to_email=user.email, token=raw_token)

    async def confirm_email_verification(self, token: str) -> None:
        record = await self.email_verifications.get_by_hash(hash_token(token))
        if record is None or record.used_at is not None or record.expires_at < datetime.now(UTC):
            raise UnauthorizedError("لینک تأیید ایمیل نامعتبر یا منقضی‌شده است.")

        user = await self.users.get_by_id(record.user_id)
        if user is None:
            raise NotFoundError("کاربر پیدا نشد.")

        user.is_verified = True
        record.used_at = datetime.now(UTC)

    async def login_or_register_with_google(self, identity: GoogleIdentity) -> User:
        existing_via_oauth = await self.users.get_by_oauth(OAuthProvider.google, identity.subject)
        if existing_via_oauth is not None:
            existing_via_oauth.last_login = datetime.now(UTC)
            return existing_via_oauth

        existing_local = await self.users.get_by_email(identity.email)
        if existing_local is not None:
            # A local account already owns this email: never auto-link on
            # login, that is exactly the account-takeover path we must avoid.
            raise ConflictError(
                "حسابی با این ایمیل از قبل وجود دارد. ابتدا با رمز عبور وارد شوید و سپس "
                "حساب گوگل را از تنظیمات پروفایل متصل کنید."
            )

        base_username = identity.email.split("@")[0][:40] or "user"
        username = base_username
        suffix = 0
        while await self.users.get_by_username(username):
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User(
            email=identity.email.lower(),
            username=username,
            hashed_password=None,
            first_name=identity.name,
            avatar=identity.picture,
            role=UserRole.customer,
            is_verified=identity.email_verified,
            last_login=datetime.now(UTC),
        )
        self.users.add(user)
        await self.session.flush()
        self.users.add_oauth_account(
            OAuthAccount(
                user_id=user.id,
                provider=OAuthProvider.google,
                provider_user_id=identity.subject,
                email=identity.email,
            )
        )
        return user

    async def link_google_account(self, user: User, identity: GoogleIdentity) -> None:
        if identity.email.lower() != user.email.lower():
            raise ConflictError("ایمیل حساب گوگل باید با ایمیل حساب کاربری یکسان باشد.")
        existing = await self.users.get_by_oauth(OAuthProvider.google, identity.subject)
        if existing is not None:
            raise ConflictError("این حساب گوگل قبلاً به کاربر دیگری متصل شده است.")
        self.users.add_oauth_account(
            OAuthAccount(
                user_id=user.id,
                provider=OAuthProvider.google,
                provider_user_id=identity.subject,
                email=identity.email,
            )
        )
