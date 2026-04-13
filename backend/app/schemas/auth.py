"""
Auth Pydantic Schemas
======================
WHY: Schemas validate and document request/response shapes.
     Keeping them separate from ORM models prevents accidentally
     exposing internal fields (like hashed_password) in API responses.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    """Schema for POST /api/auth/register"""
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        WHY: Enforce minimum password security at the API layer.
             Weak passwords are rejected before they reach the DB.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number.")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v


class LoginRequest(BaseModel):
    """Schema for POST /api/auth/login"""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Schema for POST /api/auth/refresh"""
    refresh_token: str


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class UserResponse(BaseModel):
    """
    Safe user representation for API responses.
    WHY: Explicitly lists allowed fields — hashed_password never included.
    """
    id: uuid.UUID
    email: str
    name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token pair returned on login/register."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic success message response."""
    message: str