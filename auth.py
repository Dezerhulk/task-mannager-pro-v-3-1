import re
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config import (
    ACCESS_TOKEN_EXPIRE_SECONDS,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_SECONDS,
    SECRET_KEY,
)
from database import RefreshToken as DbRefreshToken, User as DbUser

security = HTTPBearer()

PASSWORD_POLICY = {
    "min_length": 10,
    "uppercase": 1,
    "lowercase": 1,
    "digits": 1,
    "special": 1,
}


def hash_password(plain_password: str) -> str:
    """Hash a plain password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode(), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def validate_password(password: str) -> None:
    if len(password) < PASSWORD_POLICY["min_length"]:
        raise ValueError("Password must be at least 10 characters long.")
    if sum(1 for c in password if c.isupper()) < PASSWORD_POLICY["uppercase"]:
        raise ValueError("Password must contain at least one uppercase letter.")
    if sum(1 for c in password if c.islower()) < PASSWORD_POLICY["lowercase"]:
        raise ValueError("Password must contain at least one lowercase letter.")
    if sum(1 for c in password if c.isdigit()) < PASSWORD_POLICY["digits"]:
        raise ValueError("Password must contain at least one digit.")
    if sum(1 for c in password if re.match(r"[^A-Za-z0-9]", c)) < PASSWORD_POLICY["special"]:
        raise ValueError("Password must contain at least one special character.")


def authenticate_user(db: Session, username: str, password: str) -> DbUser | None:
    user = db.query(DbUser).filter(DbUser.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


def create_refresh_token(db: Session, username: str) -> str:
    jti = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_EXPIRE_SECONDS)
    payload = {
        "sub": username,
        "jti": jti,
        "exp": expires_at,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    refresh_record = DbRefreshToken(
        jti=jti,
        username=username,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(refresh_record)
    db.commit()
    return token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_refresh_token(db: Session, token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        jti = payload.get("jti")
        if not username or not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_record = db.query(DbRefreshToken).filter(DbRefreshToken.jti == jti).first()
    if not token_record or token_record.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked or invalid")
    if token_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")
    return username


def revoke_refresh_token(db: Session, token: str) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
    except jwt.InvalidTokenError:
        return

    if not jti:
        return

    token_record = db.query(DbRefreshToken).filter(DbRefreshToken.jti == jti).first()
    if token_record and not token_record.revoked:
        token_record.revoked = True
        db.commit()


def revoke_all_refresh_tokens(db: Session, username: str) -> int:
    tokens = db.query(DbRefreshToken).filter(
        DbRefreshToken.username == username,
        DbRefreshToken.revoked == False,
    ).all()
    for token_record in tokens:
        token_record.revoked = True
    if tokens:
        db.commit()
    return len(tokens)
