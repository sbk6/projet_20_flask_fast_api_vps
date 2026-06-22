from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from ..models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr = Field(..., examples=["jean.dupont@email.com"])
    username: str = Field(..., min_length=3, max_length=100, examples=["jean_dupont"])
    password: str = Field(..., min_length=8, max_length=100, examples=["MonMotDePasse123!"])
    full_name: Optional[str] = Field(None, examples=["Jean Dupont"])

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres, _ et -")
        return v.lower()

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "jean.dupont@email.com",
                "username": "jean_dupont",
                "password": "MonMotDePasse123!",
                "full_name": "Jean Dupont",
            }
        }
    }


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, examples=["Jean Dupont"])
    email: Optional[EmailStr] = Field(None, examples=["jean.dupont@email.com"])
    password: Optional[str] = Field(None, min_length=8, examples=["NouveauMotDePasse456!"])


class UserRead(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "email": "jean.dupont@email.com",
                "username": "jean_dupont",
                "full_name": "Jean Dupont",
                "role": "client",
                "is_active": True,
                "created_at": "2025-01-15T10:30:00Z",
            }
        },
    }


class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["jean.dupont@email.com"])
    password: str = Field(..., examples=["MonMotDePasse123!"])

    model_config = {
        "json_schema_extra": {
            "example": {"email": "jean.dupont@email.com", "password": "MonMotDePasse123!"}
        }
    }


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    }


class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
