"""
Vendly POS - Error Messages Constants
=====================================
Centralized error message constants to avoid hardcoding error strings.
Ensures consistency across the application and easier maintenance.
"""


class ErrorMessages:
    """All error messages used in the application"""

    # ===== Authentication & Authorization =====
    INVALID_TOKEN = "Invalid token"
    TOKEN_EXPIRED = "Token has expired"
    INVALID_CREDENTIALS = "Invalid email or password"
    AUTHENTICATION_REQUIRED = "Authentication required"
    PERMISSION_DENIED = "Permission denied"
    ACCESS_DENIED = "Access denied"

    # ===== User Errors =====
    USER_NOT_FOUND = "User not found"
    USER_ALREADY_EXISTS = "User with this email already exists"
    USER_INACTIVE = "User is inactive"
    PASSWORD_TOO_SHORT = "Password must be at least 6 characters"
    INVALID_EMAIL = "Invalid email format"

    # ===== Product Errors =====
    PRODUCT_NOT_FOUND = "Product not found"
    PRODUCT_ALREADY_EXISTS = "Product with this SKU already exists"
    PRODUCT_SKU_EXISTS = "A product with this SKU already exists"
    PRODUCT_BARCODE_EXISTS = "A product with this barcode already exists"
    PRODUCT_DUPLICATE_FIELD = "Product with duplicate unique field already exists"
    INSUFFICIENT_STOCK = "Insufficient stock for this product"
    INVALID_QUANTITY = "Invalid quantity"

    # ===== Category Errors =====
    CATEGORY_NOT_FOUND = "Category not found"
    CATEGORY_ALREADY_EXISTS = "Category with this name already exists"

    # ===== Coupon/Discount Errors =====
    COUPON_NOT_FOUND = "Coupon not found"
    COUPON_CODE_EXISTS = "Coupon code already exists"
    COUPON_EXPIRED = "Coupon has expired"
    COUPON_INVALID = "Invalid coupon code"
    COUPON_MAX_USES_EXCEEDED = "Coupon has reached maximum usage limit"
    COUPON_MIN_ORDER_NOT_MET = "Order does not meet minimum order value for this coupon"
    DISCOUNT_NOT_FOUND = "Discount not found"

    # ===== Customer Errors =====
    CUSTOMER_NOT_FOUND = "Customer not found"
    CUSTOMER_EMAIL_EXISTS = "Customer with this email already exists"
    CUSTOMER_PHONE_EXISTS = "Customer with this phone already exists"
    INVALID_PHONE = "Invalid phone number"

    # ===== Sale/Order Errors =====
    SALE_NOT_FOUND = "Sale not found"
    SALE_ALREADY_REFUNDED = "Sale has already been refunded"
    SALE_CANNOT_REFUND = "This sale cannot be refunded"
    SALE_VOID_NOT_ALLOWED = "Cannot void this sale"
    INVALID_SALE_DATA = "Invalid sale data"
    EMPTY_CART = "Cannot create sale with empty cart"
    EMPLOYEE_ID_REQUIRED = "Employee ID is required for refund processing"

    # ===== Payment Errors =====
    PAYMENT_FAILED = "Payment failed"
    PAYMENT_INVALID = "Invalid payment method"
    PAYMENT_AMOUNT_MISMATCH = "Payment amount does not match sale total"
    PAYMENT_PROCESSING_ERROR = "Error processing payment"
    STRIPE_ERROR = "Stripe payment error"
    UPI_ERROR = "UPI payment error"
    PAYMENT_GATEWAY_ERROR = "Payment gateway error"
    INVALID_PAYMENT_METHOD = "Invalid payment method"

    # ===== Inventory Errors =====
    INVENTORY_UPDATE_FAILED = "Failed to update inventory"
    STOCK_NOT_AVAILABLE = "Stock not available for this product"

    # ===== Validation Errors =====
    INVALID_REQUEST = "Invalid request"
    MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    INVALID_DATA_TYPE = "Invalid data type for field: {field}"
    INVALID_DATE_RANGE = "Invalid date range"

    # ===== Database Errors =====
    DATABASE_ERROR = "Database error occurred"
    RECORD_NOT_FOUND = "Record not found"
    DUPLICATE_ENTRY = "Duplicate entry"

    # ===== Rate Limiting =====
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again later"
    TOO_MANY_LOGIN_ATTEMPTS = "Too many login attempts. Please try again later"

    # ===== External Service Errors =====
    EXTERNAL_SERVICE_ERROR = "External service error: {service}"
    SERVICE_TEMPORARILY_UNAVAILABLE = "Service temporarily unavailable"

    # ===== Offline/Sync Errors =====
    OFFLINE_SALE_SYNC_FAILED = "Failed to sync offline sale"
    BATCH_SYNC_PARTIAL_FAILURE = "Some sales failed to sync"

    # ===== Configuration Errors =====
    CONFIGURATION_ERROR = "Configuration error"
    MISSING_CONFIGURATION = "Missing configuration: {config}"

    # ===== AI/ML Errors =====
    AI_SERVICE_ERROR = "AI service error"
    FORECAST_ERROR = "Failed to generate forecast"
    ANOMALY_DETECTION_ERROR = "Failed to perform anomaly detection"
    RECOMMENDATION_ERROR = "Failed to generate recommendations"

    # ===== Webhook Errors =====
    WEBHOOK_ERROR = "Webhook processing error"
    INVALID_WEBHOOK_SIGNATURE = "Invalid webhook signature"


class ErrorCodes:
    """Standardized error codes for API responses"""

    # Authentication
    AUTH_001 = "INVALID_TOKEN"
    AUTH_002 = "TOKEN_EXPIRED"
    AUTH_003 = "INVALID_CREDENTIALS"
    AUTH_004 = "AUTHENTICATION_REQUIRED"
    AUTH_005 = "PERMISSION_DENIED"

    # Users
    USER_001 = "USER_NOT_FOUND"
    USER_002 = "USER_ALREADY_EXISTS"
    USER_003 = "USER_INACTIVE"
    USER_004 = "INVALID_PASSWORD"

    # Products
    PRODUCT_001 = "PRODUCT_NOT_FOUND"
    PRODUCT_002 = "PRODUCT_ALREADY_EXISTS"
    PRODUCT_003 = "INSUFFICIENT_STOCK"
    PRODUCT_004 = "INVALID_QUANTITY"

    # Customers
    CUSTOMER_001 = "CUSTOMER_NOT_FOUND"
    CUSTOMER_002 = "CUSTOMER_EMAIL_EXISTS"
    CUSTOMER_003 = "INVALID_PHONE"

    # Sales
    SALE_001 = "SALE_NOT_FOUND"
    SALE_002 = "EMPTY_CART"
    SALE_003 = "INVALID_SALE_DATA"

    # Payments
    PAYMENT_001 = "PAYMENT_FAILED"
    PAYMENT_002 = "INVALID_PAYMENT_METHOD"
    PAYMENT_003 = "PAYMENT_AMOUNT_MISMATCH"

    # Validation
    VALIDATION_001 = "INVALID_REQUEST"
    VALIDATION_002 = "MISSING_REQUIRED_FIELD"
    VALIDATION_003 = "INVALID_DATA_TYPE"

    # Rate Limiting
    RATE_LIMIT_001 = "RATE_LIMIT_EXCEEDED"
    RATE_LIMIT_002 = "TOO_MANY_LOGIN_ATTEMPTS"

    # Database
    DB_001 = "DATABASE_ERROR"
    DB_002 = "DUPLICATE_ENTRY"

    # External Services
    EXTERNAL_001 = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_002 = "SERVICE_UNAVAILABLE"


class HTTPStatusCodes:
    """Standard HTTP status codes (for reference)"""

    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    RATE_LIMIT = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


def get_error_message(template: str, **kwargs) -> str:
    """Format error message with provided parameters"""
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        return template


# Usage helper function for consistent error responses
def create_error_response(
    message: str,
    status_code: int,
    error_code: str,
    details: dict = None,
) -> dict:
    """Create a standardized error response"""
    return {
        "error": {
            "message": message,
            "code": error_code,
            "status_code": status_code,
            "details": details or {},
        }
    }
