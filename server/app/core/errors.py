"""
Vendly POS - Global Error Handling
Provides centralized exception handling and error responses
"""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("vendly.errors")


class VendlyError(Exception):
    """Base exception for Vendly application errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "VENDLY_ERROR"
        self.details = details or {}
        super().__init__(message)


class NotFoundError(VendlyError):
    """Resource not found error"""

    def __init__(
        self,
        resource: str,
        identifier: Any = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource} not found"
        if identifier is not None:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError_(VendlyError):
    """Validation error"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class AuthenticationError(VendlyError):
    """Authentication error"""

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(VendlyError):
    """Authorization error"""

    def __init__(
        self,
        message: str = "Permission denied",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class ConflictError(VendlyError):
    """Conflict error (e.g., duplicate resource)"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR",
            details=details,
        )


class RateLimitError(VendlyError):
    """Rate limit exceeded error"""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_ERROR",
            details=error_details,
        )


class ExternalServiceError(VendlyError):
    """External service error (e.g., Stripe, payment gateway)"""

    def __init__(
        self,
        service: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        error_details["service"] = service
        super().__init__(
            message=f"{service} error: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
        )


def create_error_response(
    message: str,
    status_code: int,
    error_code: str = "ERROR",
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response"""
    content = {
        "error": True,
        "message": message,
        "error_code": error_code,
    }
    if details:
        content["details"] = details

    return JSONResponse(status_code=status_code, content=content)


async def vendly_exception_handler(request: Request, exc: VendlyError) -> JSONResponse:
    """Handle VendlyError exceptions"""
    logger.warning(
        f"VendlyError: {exc.error_code} - {exc.message}",
        extra={"path": request.url.path, "details": exc.details},
    )
    return create_error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException"""
    return create_error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
    )


async def starlette_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPException"""
    return create_error_response(
        message=str(exc.detail),
        status_code=exc.status_code,
        error_code="HTTP_ERROR",
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})

    return create_error_response(
        message="Validation error",
        status_code=422,
        error_code="VALIDATION_ERROR",
        details={"errors": errors},
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    logger.error(
        f"Database error: {exc}",
        extra={"path": request.url.path},
        exc_info=True,
    )

    if isinstance(exc, IntegrityError):
        # Handle unique constraint violations, foreign key violations, etc.
        message = "Database constraint violation"
        if "UNIQUE constraint" in str(exc) or "duplicate key" in str(exc).lower():
            message = "A record with this value already exists"
        elif "FOREIGN KEY constraint" in str(exc):
            message = "Referenced record does not exist"

        return create_error_response(
            message=message,
            status_code=409,
            error_code="DATABASE_CONSTRAINT_ERROR",
        )

    return create_error_response(
        message="Database error occurred",
        status_code=500,
        error_code="DATABASE_ERROR",
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions"""
    # Log the full traceback for debugging
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    # Return a generic error message to the client
    return create_error_response(
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        error_code="INTERNAL_SERVER_ERROR",
    )


def setup_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    from pydantic import ValidationError

    app.add_exception_handler(VendlyError, vendly_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
