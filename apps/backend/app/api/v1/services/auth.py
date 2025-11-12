from sqlalchemy.orm import Session
from app.db import models as m
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_password

def get_user_by_email(db: Session, email: str):
    return db.query(m.User).filter(m.User.email==email).first()

async def authenticate(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

async def register_user(db: Session, email: str, password: str, full_name: str | None, role: str = "clerk"):
    existing = get_user_by_email(db, email)
    if existing:
        return None
    user = m.User(email=email, password_hash=hash_password(password), full_name=full_name, role=role)
    db.add(user)
    db.commit(); db.refresh(user)
    return user