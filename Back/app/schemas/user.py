from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email do usuário")
    username: str = Field(
        ..., min_length=3, max_length=50, description="Nome de usuário"
    )
    password: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")

    @validator("username")
    def validate_username(cls, v):
        if not v.isalnum() and not all(c in "_-" for c in v if not c.isalnum()):
            raise ValueError("Username deve conter apenas letras, números, _ e -")
        return v


class UserLogin(BaseModel):
    username: str = Field(..., description="Nome de usuário")
    password: str = Field(..., description="Senha")


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
