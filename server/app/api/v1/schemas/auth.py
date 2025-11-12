from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal

Role = Literal["cashier","manager","admin"]

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    role: Role = "cashier"

class UserOut(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Role = "cashier"