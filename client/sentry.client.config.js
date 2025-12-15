/**
 * Sentry Configuration for Next.js
 * ================================
 * Place this file at the root of your Next.js project
 * This is loaded by the @sentry/nextjs package
 */

// This file is required by Next.js when using @sentry/nextjs
import * as Sentry from "@sentry/nextjs";

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "production",
    release: process.env.NEXT_PUBLIC_APP_VERSION || "2.0.0",
    
    // Performance monitoring
    tracesSampleRate:
      parseFloat(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
    
    // Session replay
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Debug mode
    debug: process.env.NEXT_PUBLIC_SENTRY_DEBUG === "true",

    // Before send hook
    beforeSend(event, hint) {
      // Filter sensitive data
      if (event.request?.headers) {
        const sensitiveHeaders = [
          "authorization",
          "cookie",
          "x-api-key",
          "x-auth-token",
        ];
        sensitiveHeaders.forEach((header) => {
          if (event.request.headers[header]) {
            event.request.headers[header] = "[REDACTED]";
          }
        });
      }

      return event;
    },

    // Ignore certain errors
    ignoreErrors: [
      "top.GLOBALS",
      "originalCreateNotification",
      "canvas.contentDocument",
      "MyApp_RemoveAllHighlights",
      "NetworkError",
      "TimeoutError",
      "WebSocket",
    ],

    // URLs to capture
    allowUrls: [
      /http(s)?:\/\/localhost/,
      /http(s)?:\/\/.*\.vendly\.com/,
    ],

    // URLs to ignore
    denyUrls: [/extensions\//i, /^chrome:\/\//i],

    // Integrations
    integrations: [
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
  });
}
