import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.users.models import UserRole

_USERNAME_PATTERN = r"^[a-zA-Z0-9_]{3,50}$"


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=_USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        if value.isdigit() or value.isalpha():
            raise ValueError("رمز عبور باید ترکیبی از حروف و اعداد باشد.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerificationConfirm(BaseModel):
    token: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    avatar: str | None
    role: UserRole
    is_verified: bool

    model_config = {"from_attributes": True}


class GoogleLinkConfirm(BaseModel):
    code: str
    state: str
