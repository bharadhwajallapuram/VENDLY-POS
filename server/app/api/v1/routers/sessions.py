"""
Vendly POS - Session Management API Routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.schemas.auth import UserResponse
from app.services.audit import log_session_created, log_session_ended
from app.services.session import SessionManager, SessionSecurityManager

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("/validate")
async def validate_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Validate and refresh current session"""
    session = SessionManager.get_active_session(db, current_user.id, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    # Update activity
    SessionManager.update_activity(db, session_id, current_user.id)

    return {
        "session_id": session.id,
        "is_active": session.is_active,
        "is_2fa_verified": session.is_2fa_verified,
        "last_activity": session.last_activity.isoformat(),
    }


@router.post("/end")
async def end_session(
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """End current session (logout)"""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id required",
        )

    success = SessionManager.end_session(
        db,
        session_id,
        current_user.id,
        reason="manual_logout",
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    log_session_ended(current_user.id, session_id, "manual_logout")

    return {"message": "Session ended"}


@router.get("/active")
async def get_active_sessions(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Get all active sessions for current user"""
    sessions = SessionManager.get_user_sessions(db, current_user.id)

    return [
        {
            "id": s.id,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "started_at": s.started_at.isoformat(),
            "last_activity": s.last_activity.isoformat(),
        }
        for s in sessions
    ]


@router.post("/end-all")
async def end_all_sessions(
    except_session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """End all sessions (e.g., password change, security alert)"""
    count = SessionManager.end_all_user_sessions(
        db,
        current_user.id,
        except_session_id=except_session_id,
        reason="user_requested",
    )

    log_session_ended(
        current_user.id, except_session_id or "all", "user_ended_all_sessions"
    )

    return {"message": f"Ended {count} sessions"}


@router.post("/check-suspicious")
async def check_suspicious_login(
    ip_address: str,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """Check if login is from suspicious IP"""
    is_suspicious = SessionSecurityManager.detect_suspicious_activity(
        db,
        current_user.id,
        ip_address,
    )

    if is_suspicious:
        from app.services.audit import log_security_alert

        log_security_alert(
            event_type="suspicious_login",
            user_id=current_user.id,
            ip_address=ip_address,
        )

    return {
        "is_suspicious": is_suspicious,
        "message": (
            (
                "Login from a new location detected. "
                "A verification email has been sent."
            )
            if is_suspicious
            else "Login recognized"
        ),
    }
