from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db import models
from app.db.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == payload.get("sub")).first()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: str):
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role.value not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions for this action.")
        return user
    return checker


def get_owned_contract(db: Session, contract_id: str, user: models.User) -> models.Contract:
    """Fetch a contract, scoped to the requesting user. Every route that
    touches a specific contract (or its clauses/chat/compliance/audit
    history) must go through this instead of querying Contract by id
    alone — otherwise any authenticated user can view or act on any other
    user's contracts just by knowing/guessing the id."""
    contract = (
        db.query(models.Contract)
        .filter(models.Contract.id == contract_id, models.Contract.uploaded_by_id == user.id)
        .first()
    )
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return contract
