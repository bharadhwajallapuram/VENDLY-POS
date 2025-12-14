from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

Role = Literal["clerk", "cashier", "manager", "admin"]


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TwoFactorRequiredResponse(BaseModel):
    """Response when 2FA is required for login"""

    requires_2fa: bool = True
    user_id: int
    email: str
    temp_token: str  # Temporary token to verify 2FA, expires in 5 minutes


class TwoFactorVerifyLoginIn(BaseModel):
    """Verify 2FA code during login"""

    temp_token: str
    token: str = Field(..., min_length=6, max_length=6)  # TOTP code
    backup_code: Optional[str] = None  # Alternative: backup code


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    role: Role = "cashier"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    role: Role = "cashier"
