"""
Vendly POS - Session Management Service
Handles session timeouts, tracking, and validation
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models as m

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions and timeouts"""

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        ip_address: str,
        user_agent: str,
        is_2fa_verified: bool = False,
    ) -> m.UserSession:
        """Create a new user session"""
        session = m.UserSession(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            last_activity=datetime.now(UTC),
            is_active=True,
            is_2fa_verified=is_2fa_verified,
            started_at=datetime.now(UTC),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Session created for user {user_id} from {ip_address}")
        return session

    @staticmethod
    def get_active_session(
        db: Session,
        user_id: int,
        session_id: str,
    ) -> Optional[m.UserSession]:
        """Get an active session, return None if expired"""
        session = (
            db.query(m.UserSession)
            .filter(
                m.UserSession.id == session_id,
                m.UserSession.user_id == user_id,
                m.UserSession.is_active == True,
            )
            .first()
        )

        if not session:
            return None

        # Check if session has expired due to inactivity (configurable timeout)
        timeout_delta = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        if datetime.now(UTC) - session.last_activity > timeout_delta:
            session.is_active = False
            session.ended_at = datetime.now(UTC)
            session.timeout_reason = "inactivity"
            db.commit()

            logger.warning(f"Session {session_id} timed out due to inactivity")
            return None

        return session

    @staticmethod
    def update_activity(
        db: Session,
        session_id: str,
        user_id: int,
    ) -> bool:
        """Update session activity timestamp"""
        session = (
            db.query(m.UserSession)
            .filter(
                m.UserSession.id == session_id,
                m.UserSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            return False

        session.last_activity = datetime.now(UTC)
        db.commit()
        return True

    @staticmethod
    def end_session(
        db: Session,
        session_id: str,
        user_id: int,
        reason: str = "manual_logout",
    ) -> bool:
        """End a user session"""
        session = (
            db.query(m.UserSession)
            .filter(
                m.UserSession.id == session_id,
                m.UserSession.user_id == user_id,
            )
            .first()
        )

        if not session:
            return False

        session.is_active = False
        session.ended_at = datetime.now(UTC)
        session.timeout_reason = reason
        db.commit()

        logger.info(f"Session {session_id} ended for user {user_id} (reason: {reason})")
        return True

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> list[m.UserSession]:
        """Get all active sessions for a user"""
        return (
            db.query(m.UserSession)
            .filter(
                m.UserSession.user_id == user_id,
                m.UserSession.is_active == True,
            )
            .all()
        )

    @staticmethod
    def end_all_user_sessions(
        db: Session,
        user_id: int,
        except_session_id: Optional[str] = None,
        reason: str = "admin_logout",
    ) -> int:
        """
        End all sessions for a user (e.g., password change, security event)

        Args:
            db: Database session
            user_id: User ID
            except_session_id: Session ID to keep active (optional)
            reason: Reason for ending sessions

        Returns:
            Number of sessions ended
        """
        sessions = db.query(m.UserSession).filter(
            m.UserSession.user_id == user_id,
            m.UserSession.is_active == True,
        )

        if except_session_id:
            sessions = sessions.filter(m.UserSession.id != except_session_id)

        sessions_list = sessions.all()
        count = len(sessions_list)

        for session in sessions_list:
            session.is_active = False
            session.ended_at = datetime.now(UTC)
            session.timeout_reason = reason

        db.commit()

        logger.warning(f"Ended {count} sessions for user {user_id} (reason: {reason})")
        return count

    @staticmethod
    def cleanup_expired_sessions(db: Session, days: int = 30) -> int:
        """
        Clean up old expired sessions

        Args:
            db: Database session
            days: How many days of old sessions to keep

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        expired = (
            db.query(m.UserSession)
            .filter(
                m.UserSession.is_active == False,
                m.UserSession.ended_at < cutoff_date,
            )
            .all()
        )

        count = len(expired)
        for session in expired:
            db.delete(session)

        db.commit()

        logger.info(f"Cleaned up {count} expired sessions")
        return count


class SessionSecurityManager:
    """Enhanced session security features"""

    @staticmethod
    def detect_suspicious_activity(
        db: Session,
        user_id: int,
        new_ip: str,
    ) -> bool:
        """
        Detect if login is from a new IP address
        Returns True if suspicious (new IP), False if known
        """
        last_session = (
            db.query(m.UserSession)
            .filter(
                m.UserSession.user_id == user_id,
                m.UserSession.is_active == True,
            )
            .order_by(m.UserSession.started_at.desc())
            .first()
        )

        if not last_session:
            return False  # No previous session, not suspicious

        return last_session.ip_address != new_ip

    @staticmethod
    def require_reauthentication(
        db: Session,
        user_id: int,
        reason: str = "sensitive_operation",
    ) -> bool:
        """
        Force user to re-authenticate for sensitive operations
        Ends all sessions and logs security event
        """
        SessionManager.end_all_user_sessions(
            db,
            user_id,
            reason=reason,
        )

        logger.warning(
            f"Reauthentication required for user {user_id} " f"(reason: {reason})"
        )
        return True
