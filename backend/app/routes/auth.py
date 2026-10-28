"""Auth routes — login, refresh, logout."""

from fastapi import APIRouter, HTTPException, status, Response, Request

from app.models.user import User
from app.auth.password import verify_password
from app.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest
from app.schemas.common import APIResponse

router = APIRouter()


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    user = await User.find_one(User.username == body.username, User.is_active == True)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return APIResponse(data={
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
        }
    })


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await User.find_one(User.id == int(payload["sub"]), User.is_active == True)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    return APIResponse(data={"access_token": access_token, "token_type": "bearer"})


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return APIResponse(message="Logged out")
