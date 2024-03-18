import jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from billing import crud
from billing.db import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db: Session = Depends(get_db), session_token: str | None = Cookie(default=None)):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    token = jwt.decode(session_token, "secret", algorithm="HS256")
    user_id = token["user_id"]
    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return user
