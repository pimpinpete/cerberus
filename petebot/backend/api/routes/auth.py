"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta

from ..dependencies import get_container_dep
from ...core.container import DIContainer
from ...core.security import SecurityManager

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    container: DIContainer = Depends(get_container_dep)
):
    """Login and get access token."""
    security = container.get(SecurityManager)

    # DEMO ENDPOINT: accepts any credentials. Production would validate against a user database.
    if request.email and request.password:
        token = security.create_jwt(
            payload={"sub": request.email, "email": request.email},
            expires_in=timedelta(hours=24)
        )
        return TokenResponse(
            access_token=token,
            expires_in=86400
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    container: DIContainer = Depends(get_container_dep)
):
    """Refresh access token."""
    security = container.get(SecurityManager)

    # TODO: Implement proper refresh token logic
    token = security.create_jwt(
        payload={"sub": "user@example.com"},
        expires_in=timedelta(hours=24)
    )
    return TokenResponse(
        access_token=token,
        expires_in=86400
    )


@router.post("/logout")
async def logout():
    """Logout (client-side token deletion)."""
    return {"status": "ok", "message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    container: DIContainer = Depends(get_container_dep)
):
    """Get current user info."""
    # TODO: Implement proper user lookup
    return UserResponse(
        id="1",
        email="user@example.com",
        name="Andrew Peterson"
    )
