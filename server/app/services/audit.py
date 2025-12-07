"""
Vendly POS - Audit Logging Service
Tracks sensitive operations for security and compliance
"""
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from app.core.config import settings


class AuditAction(str, Enum):
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_DEACTIVATED = "user_deactivated"
    PASSWORD_CHANGED = "password_changed"
    
    # Product management
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    
    # Sales
    SALE_COMPLETED = "sale_completed"
    SALE_VOIDED = "sale_voided"
    SALE_REFUNDED = "sale_refunded"
    
    # Customer management
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    CUSTOMER_DELETED = "customer_deleted"
    LOYALTY_ADJUSTED = "loyalty_adjusted"
    
    # System
    SETTINGS_CHANGED = "settings_changed"
    DATA_EXPORT = "data_export"


# Configure audit logger
audit_logger = logging.getLogger("vendly.audit")
audit_logger.setLevel(logging.INFO)

# Create console handler if not already configured
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)
    
    # Also log to file
    try:
        file_handler = logging.FileHandler('audit.log')
        file_handler.setLevel(logging.INFO)
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
        "timestamp": datetime.utcnow().isoformat(),
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
    log_audit(AuditAction.LOGIN_SUCCESS, user_id=user_id, user_email=email, ip_address=ip)


def log_login_failed(email: str, ip: Optional[str] = None, reason: str = "invalid_credentials"):
    log_audit(
        AuditAction.LOGIN_FAILED,
        user_email=email,
        ip_address=ip,
        details={"reason": reason},
        success=False
    )


def log_user_created(admin_id: int, new_user_id: int, new_user_email: str, role: str):
    log_audit(
        AuditAction.USER_CREATED,
        user_id=admin_id,
        target_type="user",
        target_id=new_user_id,
        details={"email": new_user_email, "role": role}
    )


def log_user_deleted(admin_id: int, deleted_user_id: int, deleted_email: str):
    log_audit(
        AuditAction.USER_DELETED,
        user_id=admin_id,
        target_type="user",
        target_id=deleted_user_id,
        details={"deleted_email": deleted_email}
    )


def log_product_change(user_id: int, action: AuditAction, product_id: int, product_name: str):
    log_audit(
        action,
        user_id=user_id,
        target_type="product",
        target_id=product_id,
        details={"name": product_name}
    )


def log_sale_event(user_id: int, action: AuditAction, sale_id: int, total: float):
    log_audit(
        action,
        user_id=user_id,
        target_type="sale",
        target_id=sale_id,
        details={"total": total}
    )
