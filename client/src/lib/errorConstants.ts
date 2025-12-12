/**
 * Vendly POS - Frontend Error Messages Constants
 * =============================================
 * Centralized error message constants for frontend to avoid hardcoding.
 * Ensures consistency with backend errors and easier maintenance.
 */

export const ErrorMessages = {
  // ===== Authentication & Authorization =====
  INVALID_TOKEN: "Invalid token",
  TOKEN_EXPIRED: "Token has expired",
  INVALID_CREDENTIALS: "Invalid email or password",
  AUTHENTICATION_REQUIRED: "Authentication required",
  PERMISSION_DENIED: "Permission denied",
  ACCESS_DENIED: "Access denied",

  // ===== User Errors =====
  USER_NOT_FOUND: "User not found",
  USER_ALREADY_EXISTS: "User with this email already exists",
  USER_INACTIVE: "User is inactive",
  PASSWORD_TOO_SHORT: "Password must be at least 6 characters",
  INVALID_EMAIL: "Invalid email format",

  // ===== Product Errors =====
  PRODUCT_NOT_FOUND: "Product not found",
  PRODUCT_ALREADY_EXISTS: "Product with this SKU already exists",
  PRODUCT_SKU_EXISTS: "A product with this SKU already exists",
  PRODUCT_BARCODE_EXISTS: "A product with this barcode already exists",
  INSUFFICIENT_STOCK: "Insufficient stock for this product",
  INVALID_QUANTITY: "Invalid quantity",

  // ===== Category Errors =====
  CATEGORY_NOT_FOUND: "Category not found",
  CATEGORY_ALREADY_EXISTS: "Category with this name already exists",

  // ===== Coupon/Discount Errors =====
  COUPON_NOT_FOUND: "Coupon not found",
  COUPON_CODE_EXISTS: "Coupon code already exists",
  COUPON_EXPIRED: "Coupon has expired",
  COUPON_INVALID: "Invalid coupon code",
  COUPON_MAX_USES_EXCEEDED: "Coupon has reached maximum usage limit",
  DISCOUNT_NOT_FOUND: "Discount not found",

  // ===== Customer Errors =====
  CUSTOMER_NOT_FOUND: "Customer not found",
  CUSTOMER_EMAIL_EXISTS: "Customer with this email already exists",
  INVALID_PHONE: "Invalid phone number",

  // ===== Sale/Order Errors =====
  SALE_NOT_FOUND: "Sale not found",
  SALE_ALREADY_REFUNDED: "Sale has already been refunded",
  EMPTY_CART: "Cannot create sale with empty cart",
  EMPLOYEE_ID_REQUIRED: "Employee ID is required for refund processing",

  // ===== Payment Errors =====
  PAYMENT_FAILED: "Payment failed",
  PAYMENT_INVALID: "Invalid payment method",
  PAYMENT_AMOUNT_MISMATCH: "Payment amount does not match sale total",
  PAYMENT_PROCESSING_ERROR: "Error processing payment",

  // ===== Inventory Errors =====
  INVENTORY_UPDATE_FAILED: "Failed to update inventory",
  STOCK_NOT_AVAILABLE: "Stock not available for this product",

  // ===== Validation Errors =====
  INVALID_REQUEST: "Invalid request",
  MISSING_REQUIRED_FIELD: "Missing required field",
  INVALID_DATA_TYPE: "Invalid data type",
  INVALID_DATE_RANGE: "Invalid date range",

  // ===== Network Errors =====
  NETWORK_ERROR: "Network error. Please check your connection.",
  REQUEST_TIMEOUT: "Request timed out. Please try again.",
  SERVER_ERROR: "Server error. Please try again later.",

  // ===== Offline/Sync Errors =====
  OFFLINE_MODE: "You are currently offline",
  OFFLINE_SALE_SYNC_FAILED: "Failed to sync offline sale",
  SYNC_IN_PROGRESS: "Sync is in progress",
  SYNC_COMPLETED: "Sync completed successfully",
  SYNC_PARTIAL_FAILURE: "Some sales failed to sync",

  // ===== UI Errors =====
  FORM_VALIDATION_ERROR: "Please correct the errors in the form",
  REQUIRED_FIELD: "This field is required",
  INVALID_FORMAT: "Invalid format",

  // ===== Success Messages =====
  SUCCESS: "Operation completed successfully",
  CREATED_SUCCESS: "Created successfully",
  UPDATED_SUCCESS: "Updated successfully",
  DELETED_SUCCESS: "Deleted successfully",
} as const;

export const ErrorCodes = {
  // Authentication
  AUTH_001: "INVALID_TOKEN",
  AUTH_002: "TOKEN_EXPIRED",
  AUTH_003: "INVALID_CREDENTIALS",

  // Users
  USER_001: "USER_NOT_FOUND",
  USER_002: "USER_ALREADY_EXISTS",

  // Products
  PRODUCT_001: "PRODUCT_NOT_FOUND",
  PRODUCT_002: "INSUFFICIENT_STOCK",

  // Network
  NETWORK_001: "NETWORK_ERROR",
  NETWORK_002: "REQUEST_TIMEOUT",
  NETWORK_003: "SERVER_ERROR",

  // Offline
  OFFLINE_001: "OFFLINE_MODE",
  OFFLINE_002: "SYNC_FAILED",
} as const;

/**
 * Get error message with optional parameter substitution
 */
export function getErrorMessage(
  message: string,
  params?: Record<string, string | number>
): string {
  if (!params) return message;

  let result = message;
  Object.entries(params).forEach(([key, value]) => {
    result = result.replace(`{${key}}`, String(value));
  });
  return result;
}

/**
 * Format API error response to user-friendly message
 */
export function formatApiError(error: any): string {
  if (!error) return ErrorMessages.SERVER_ERROR;

  // Handle error object with detail property
  if (error.detail) {
    return typeof error.detail === "string"
      ? error.detail
      : error.detail.message || ErrorMessages.SERVER_ERROR;
  }

  // Handle error message
  if (error.message) {
    return error.message;
  }

  // Handle response status
  if (error.status === 401) {
    return ErrorMessages.INVALID_CREDENTIALS;
  }

  if (error.status === 403) {
    return ErrorMessages.PERMISSION_DENIED;
  }

  if (error.status === 404) {
    return ErrorMessages.PRODUCT_NOT_FOUND;
  }

  if (error.status === 409) {
    return ErrorMessages.PRODUCT_ALREADY_EXISTS;
  }

  if (error.status === 422) {
    return ErrorMessages.FORM_VALIDATION_ERROR;
  }

  if (error.status === 429) {
    return "Too many requests. Please try again later.";
  }

  if (error.status >= 500) {
    return ErrorMessages.SERVER_ERROR;
  }

  return ErrorMessages.INVALID_REQUEST;
}

/**
 * Log error with context for debugging
 */
export function logError(
  context: string,
  error: any,
  additionalInfo?: Record<string, any>
): void {
  const errorData = {
    timestamp: new Date().toISOString(),
    context,
    message: error?.message || error?.detail || String(error),
    status: error?.status,
    code: error?.code,
    ...additionalInfo,
  };

  console.error("[ERROR]", errorData);

  // In production, send to error tracking service (e.g., Sentry)
  if (process.env.NODE_ENV === "production") {
    // TODO: Implement error tracking
    // sentry.captureException(error, { contexts: { errorData } });
  }
}

/**
 * Retry logic for failed requests
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      const isLastAttempt = attempt === maxRetries - 1;
      const shouldRetry =
        error?.status === 429 || // Rate limited
        error?.status >= 500; // Server error

      if (!shouldRetry || isLastAttempt) {
        throw error;
      }

      // Exponential backoff
      const delay = initialDelay * Math.pow(2, attempt);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw new Error("Retry failed");
}
