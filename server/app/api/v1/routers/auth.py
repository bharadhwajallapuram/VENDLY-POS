from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth import LoginIn, TokenOut, UserOut
from app.core.deps import get_current_user, get_db
from app.services.auth import authenticate
from app.services.rate_limit import rate_limit, get_client_ip
from app.services.audit import log_login_success, log_login_failed

router = APIRouter()


@router.post("/login", response_model=TokenOut)
async def login(
    request: Request,
    payload: LoginIn,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("5/minute")),  # 5 attempts per minute per IP
):
    ip = get_client_ip(request)
    result = await authenticate(db, payload.email, payload.password)
    
    if not result:
        log_login_failed(payload.email, ip=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Log successful login
    log_login_success(result["user_id"], payload.email, ip=ip)
    
    return result


# Public registration disabled - users are created by admin only via /api/v1/users


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(email=user.email, full_name=user.full_name, role=user.role)
