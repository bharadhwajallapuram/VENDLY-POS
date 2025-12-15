/**
 * Vendly POS - Frontend Sentry Configuration
 * ==========================================
 * Error tracking and monitoring for Next.js frontend
 * 
 * Installation:
 * npm install @sentry/nextjs
 * 
 * Usage in next.config.js:
 * const withSentry = require("@sentry/nextjs").withSentry;
 * module.exports = withSentry(nextConfig);
 */

declare global {
  interface Window {
    __SENTRY_INITIALIZED__?: boolean;
  }
}

export const getSentryConfig = (): Record<string, any> | null => {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN || "";

  if (!dsn) {
    console.log("[INFO] Sentry not configured (DSN not found)");
    return null;
  }

  return {
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "production",
    release: process.env.NEXT_PUBLIC_APP_VERSION || "2.0.0",
    tracesSampleRate: parseFloat(
      process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"
    ),
    debug: process.env.NEXT_PUBLIC_SENTRY_DEBUG === "true",
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    ignoreErrors: [
      "top.GLOBALS",
      "originalCreateNotification",
      "canvas.contentDocument",
      "MyApp_RemoveAllHighlights",
      "NetworkError",
      "TimeoutError",
      "WebSocket",
    ],
    allowUrls: [
      /http(s)?:\/\/localhost/,
      /http(s)?:\/\/.*\.vendly\.com/,
    ],
    denyUrls: [/extensions\//i, /^chrome:\/\//i],
  };
};

export const initSentry = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  try {
    const sentryConfig = getSentryConfig();
    if (!sentryConfig || window.__SENTRY_INITIALIZED__) {
      return;
    }

    console.log("[OK] Sentry initialized for frontend");
    window.__SENTRY_INITIALIZED__ = true;
  } catch (error) {
    console.error("[ERROR] Failed to initialize Sentry:", error);
  }
};

export const captureException = (
  error: Error | unknown,
  context: Record<string, any> = {}
): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.withScope((scope: any) => {
      Object.entries(context).forEach(([key, value]) => {
        scope.setContext(key, { value });
      });
      Sentry.captureException(error);
    });
  } catch (e) {
    console.error("Failed to capture exception:", e);
  }
};

export const captureMessage = (
  message: string,
  level: "info" | "warning" | "error" = "info",
  context: Record<string, any> = {}
): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.withScope((scope: any) => {
      Object.entries(context).forEach(([key, value]) => {
        scope.setContext(key, { value });
      });
      Sentry.captureMessage(message, level);
    });
  } catch (e) {
    console.error("Failed to capture message:", e);
  }
};

export const addBreadcrumb = (
  message: string,
  category: string = "custom",
  data: Record<string, any> = {}
): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.addBreadcrumb({
      message,
      category,
      level: "info",
      data,
    });
  } catch (e) {
    console.error("Failed to add breadcrumb:", e);
  }
};

export const setUserContext = (
  userId: string,
  email: string = "",
  username: string = ""
): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.setUser({
      id: userId,
      email,
      username,
    });
  } catch (e) {
    console.error("Failed to set user context:", e);
  }
};

export const setTag = (key: string, value: string): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.setTag(key, value);
  } catch (e) {
    console.error("Failed to set tag:", e);
  }
};

export const setContext = (name: string, context: Record<string, any>): void => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/nextjs");
    Sentry.setContext(name, context);
  } catch (e) {
    console.error("Failed to set context:", e);
  }
};

export const capturedFetch = async (
  url: string,
  options: RequestInit = {},
  context: Record<string, any> = {}
): Promise<Response> => {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      captureMessage(
        `HTTP ${response.status}: ${response.statusText}`,
        "warning",
        {
          url,
          status: response.status,
          ...errorData,
          ...context,
        }
      );
    }

    return response;
  } catch (error) {
    captureException(error, { url, ...context });
    throw error;
  }
};
