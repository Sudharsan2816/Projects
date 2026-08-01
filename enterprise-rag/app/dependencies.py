"""FastAPI dependencies."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.models import AuditSessionLocal, AuthSessionLocal, EnterpriseSessionLocal, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_auth_db() -> Generator[Session, None, None]:
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_enterprise_db() -> Generator[Session, None, None]:
    db = EnterpriseSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_audit_db() -> Generator[Session, None, None]:
    db = AuditSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_auth_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise credentials_error
    except ValueError as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise credentials_error
    return user
