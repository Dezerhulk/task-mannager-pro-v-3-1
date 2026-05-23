"""Authentication router."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..database_pro import get_db
from ..models_pro import User
from ..schemas_pro import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RevokeRefreshTokensRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from ..crud_pro import (
    authenticate_user,
    create_audit_log,
    create_user,
    get_refresh_token,
    get_user,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    revoke_user_refresh_tokens,
    save_refresh_token,
)
from ..models_pro import UserRoleEnum
from ..auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_refresh_token,
)
from ..config import settings
from ..security import auth_rate_limit

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[auth_rate_limit("register")],
)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user_create = UserCreate(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    user = create_user(db, user_create)
    create_audit_log(db, user.id, "user", "register")
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse, dependencies=[auth_rate_limit("login")])
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login user and return tokens."""
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        attempted_user = db.query(User).filter(User.email == payload.email).first()
        create_audit_log(
            db,
            attempted_user.id if attempted_user else None,
            "user",
            "failed_login",
            new_values={"email": payload.email, "ip": request.client.host if request.client else "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    refresh_token, jti = create_refresh_token(user.id)
    save_refresh_token(db, user.id, jti, datetime.now(timezone.utc) + settings.refresh_token_expire)
    create_audit_log(db, user.id, "user", "login")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[auth_rate_limit("refresh")])
async def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    token_data = verify_refresh_token(payload.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id, jti = token_data
    refresh_record = get_refresh_token(db, jti)
    if not refresh_record or refresh_record.is_revoked or refresh_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or revoked",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    revoke_refresh_token(db, jti)
    access_token = create_access_token(user.id)
    new_refresh_token, new_jti = create_refresh_token(user.id)
    save_refresh_token(db, user.id, new_jti, datetime.now(timezone.utc) + settings.refresh_token_expire)
    create_audit_log(db, user.id, "user", "refresh")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    payload: RefreshRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke the active refresh token."""
    token_data = verify_refresh_token(payload.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id, jti = token_data
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token does not belong to the authenticated user",
        )

    if not revoke_refresh_token(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token already revoked or invalid",
        )

    create_audit_log(db, current_user_id, "user", "logout")
    return {"message": "Logged out"}


@router.post("/logout/all")
async def logout_all(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout and revoke all refresh tokens for the current user."""
    revoked_count = revoke_user_refresh_tokens(db, current_user_id)
    create_audit_log(db, current_user_id, "user", "logout_all")
    return {"message": "Logged out from all sessions", "revoked": revoked_count}


@router.post("/admin/revoke-refresh-tokens")
async def admin_revoke_refresh_tokens(
    payload: RevokeRefreshTokensRequest,
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin: revoke all refresh tokens globally or for a specific user."""
    current_user = get_user(db, current_user_id)
    if not current_user or current_user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    revoked_count = revoke_all_refresh_tokens(db, user_id=payload.user_id)
    create_audit_log(
        db,
        current_user_id,
        "user",
        "revoke_refresh_tokens",
        new_values={
            "target_user_id": payload.user_id,
            "revoked": revoked_count,
        },
    )
    scope = f"user {payload.user_id}" if payload.user_id is not None else "all users"
    return {
        "message": f"Revoked refresh tokens for {scope}",
        "revoked": revoked_count,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)