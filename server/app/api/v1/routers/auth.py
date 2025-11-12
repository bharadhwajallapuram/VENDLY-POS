from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.core.deps import get_current_user, get_db
from app.services.auth import authenticate, register_user

router = APIRouter()


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: Session = Depends(get_db)):
    tokens = await authenticate(db, payload.email, payload.password)
    if not tokens:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return tokens


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user = await register_user(
        db, payload.email, payload.password, payload.full_name, payload.role
    )
    if not user:
        raise HTTPException(status_code=409, detail="Email already exists")
    return UserOut(email=user.email, full_name=user.full_name, role=user.role)


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(email=user["email"], full_name=user["full_name"], role=user["role"])
