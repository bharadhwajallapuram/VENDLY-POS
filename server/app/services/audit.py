"""
Vendly POS - Audit Logging Service
Tracks sensitive operations for security and compliance
"""

import json
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from app.core.config import settings


class AuditAction(str, Enum):
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    TWO_FACTOR_VERIFIED = "two_factor_verified"

    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_DEACTIVATED = "user_deactivated"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"

    # Product management
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"

    # Sales & Transactions (SENSITIVE)
    SALE_COMPLETED = "sale_completed"
    SALE_VOIDED = "sale_voided"  # SENSITIVE
    SALE_REFUNDED = "sale_refunded"  # SENSITIVE
    DISCOUNT_APPLIED = "discount_applied"  # SENSITIVE
    DISCOUNT_REMOVED = "discount_removed"
    MANUAL_ADJUSTMENT = "manual_adjustment"  # SENSITIVE

    # Payment
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"  # SENSITIVE

    # Customer management
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_DELETED = "customer_deleted"
    LOYALTY_ADJUSTED = "loyalty_adjusted"  # SENSITIVE

    # Sessions
    SESSION_CREATED = "session_created"
    SESSION_ENDED = "session_ended"
    SESSION_TIMEOUT = "session_timeout"

    # System
    SETTINGS_CHANGED = "settings_changed"
    DATA_EXPORT = "data_export"
    SECURITY_ALERT = "security_alert"


# Configure audit logger
audit_logger = logging.getLogger("vendly.audit")
log_level = getattr(logging, settings.AUDIT_LOG_LEVEL.upper(), logging.INFO)
audit_logger.setLevel(log_level)

# Create console handler if not already configured
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - AUDIT - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)

    # Also log to file (configurable location)
    if settings.AUDIT_LOG_ENABLED:
        try:
            file_handler = logging.FileHandler(settings.AUDIT_LOG_FILE)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            audit_logger.addHandler(file_handler)
        except Exception:
            pass  # File logging optional


def log_audit(
    action: AuditAction,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
):
    """
    Log an audit event

    Args:
        action: The action being performed
        user_id: ID of the user performing the action
        user_email: Email of the user performing the action
        target_type: Type of object being acted upon (e.g., "user", "product")
        target_id: ID of the object being acted upon
        details: Additional details about the action
        ip_address: IP address of the request
        success: Whether the action succeeded
    """
    if not settings.AUDIT_LOG_ENABLED:
        return

    audit_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action.value,
        "success": success,
        "user_id": user_id,
        "user_email": user_email,
        "target_type": target_type,
        "target_id": target_id,
        "ip_address": ip_address,
        "details": details,
    }

    # Remove None values for cleaner logs
    audit_entry = {k: v for k, v in audit_entry.items() if v is not None}

    # Log as JSON for easy parsing
    audit_logger.info(json.dumps(audit_entry))

    return audit_entry


# Convenience functions for common operations
def log_login_success(user_id: int, email: str, ip: Optional[str] = None):
    log_audit(
        AuditAction.LOGIN_SUCCESS, user_id=user_id, user_email=email, ip_address=ip
    )


def log_login_failed(
    email: str, ip: Optional[str] = None, reason: str = "invalid_credentials"
):
    log_audit(
        AuditAction.LOGIN_FAILED,
        user_email=email,
        ip_address=ip,
        details={"reason": reason},
        success=False,
    )


def log_user_created(admin_id: int, new_user_id: int, new_user_email: str, role: str):
    log_audit(
        AuditAction.USER_CREATED,
        user_id=admin_id,
        target_type="user",
        target_id=new_user_id,
        details={"email": new_user_email, "role": role},
    )


def log_user_deleted(admin_id: int, deleted_user_id: int, deleted_email: str):
    log_audit(
        AuditAction.USER_DELETED,
        user_id=admin_id,
        target_type="user",
        target_id=deleted_user_id,
        details={"deleted_email": deleted_email},
    )


def log_product_change(
    user_id: int, action: AuditAction, product_id: int, product_name: str
):
    log_audit(
        action,
        user_id=user_id,
        target_type="product",
        target_id=product_id,
        details={"name": product_name},
    )


def log_sale_event(user_id: int, action: AuditAction, sale_id: int, total: float):
    log_audit(
        action,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={"total": total},
    )


# ============================================================
# SENSITIVE OPERATIONS LOGGING (Void, Refund, Discount, etc)
# ============================================================


def log_sale_void(
    user_id: int,
    sale_id: int,
    original_total: float,
    reason: str,
    authorized_by: Optional[int] = None,
):
    """Log sale void (SENSITIVE - requires approval)"""
    log_audit(
        AuditAction.SALE_VOIDED,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={
            "original_total": original_total,
            "reason": reason,
            "authorized_by": authorized_by,
        },
    )


def log_refund(
    user_id: int,
    sale_id: int,
    refund_amount: float,
    reason: str,
    payment_method: str = "original",
):
    """Log refund (SENSITIVE - tracked for compliance)"""
    log_audit(
        AuditAction.SALE_REFUNDED,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={
            "refund_amount": refund_amount,
            "reason": reason,
            "payment_method": payment_method,
        },
    )


def log_discount_applied(
    user_id: int,
    sale_id: int,
    discount_amount: float,
    discount_type: str,
    discount_code: Optional[str] = None,
):
    """Log discount application (SENSITIVE - tracking for revenue impact)"""
    log_audit(
        AuditAction.DISCOUNT_APPLIED,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={
            "discount_amount": discount_amount,
            "discount_type": discount_type,
            "discount_code": discount_code,
        },
    )


def log_discount_removed(
    user_id: int,
    sale_id: int,
    discount_amount: float,
):
    """Log discount removal"""
    log_audit(
        AuditAction.DISCOUNT_REMOVED,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={"discount_amount": discount_amount},
    )


def log_manual_adjustment(
    user_id: int,
    target_type: str,
    target_id: int,
    adjustment_type: str,
    adjustment_amount: float,
    reason: str,
):
    """Log manual adjustment (SENSITIVE - direct amount changes)"""
    log_audit(
        AuditAction.MANUAL_ADJUSTMENT,
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        details={
            "adjustment_type": adjustment_type,
            "adjustment_amount": adjustment_amount,
            "reason": reason,
        },
    )


def log_payment_refund(
    user_id: int,
    payment_id: int,
    refund_amount: float,
    refund_reason: str,
):
    """Log payment refund (SENSITIVE)"""
    log_audit(
        AuditAction.PAYMENT_REFUNDED,
        user_id=user_id,
        target_type="payment",
        target_id=payment_id,
        details={
            "refund_amount": refund_amount,
            "refund_reason": refund_reason,
        },
    )


def log_loyalty_adjustment(
    user_id: int,
    customer_id: int,
    points_adjusted: int,
    reason: str,
):
    """Log loyalty points adjustment (SENSITIVE)"""
    log_audit(
        AuditAction.LOYALTY_ADJUSTED,
        user_id=user_id,
        target_type="customer",
        target_id=customer_id,
        details={
            "points_adjusted": points_adjusted,
            "reason": reason,
        },
    )


# ============================================================
# SESSION & AUTHENTICATION LOGGING
# ============================================================


def log_session_created(user_id: int, session_id: str, ip_address: str):
    """Log session creation"""
    log_audit(
        AuditAction.SESSION_CREATED,
        user_id=user_id,
        details={"session_id": session_id},
        ip_address=ip_address,
    )


def log_session_ended(user_id: int, session_id: str, reason: str = "logout"):
    """Log session termination"""
    log_audit(
        AuditAction.SESSION_ENDED,
        user_id=user_id,
        details={
            "session_id": session_id,
            "reason": reason,
        },
    )


def log_session_timeout(user_id: int, session_id: str):
    """Log session timeout"""
    log_audit(
        AuditAction.SESSION_TIMEOUT,
        user_id=user_id,
        details={"session_id": session_id},
    )


def log_two_factor_enabled(user_id: int):
    """Log 2FA enablement"""
    log_audit(
        AuditAction.TWO_FACTOR_ENABLED,
        user_id=user_id,
    )


def log_two_factor_disabled(user_id: int, admin_id: Optional[int] = None):
    """Log 2FA disablement"""
    log_audit(
        AuditAction.TWO_FACTOR_DISABLED,
        user_id=user_id,
        details={"disabled_by": admin_id},
    )


def log_two_factor_verified(user_id: int, method: str = "totp"):
    """Log 2FA verification"""
    log_audit(
        AuditAction.TWO_FACTOR_VERIFIED,
        user_id=user_id,
        details={"method": method},
    )


def log_security_alert(
    event_type: str,
    user_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """Log security alert or anomaly"""
    log_audit(
        AuditAction.SECURITY_ALERT,
        user_id=user_id,
        details={
            "event_type": event_type,
            **(details or {}),
        },
        ip_address=ip_address,
    )
