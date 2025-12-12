/**
 * Vendly POS - Session Timeout Hook
 * Auto-logout after inactivity
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useRouter } from 'next/navigation';

interface UseSessionTimeoutOptions {
  /**
   * Session timeout in minutes (default: 15)
   */
  timeoutMinutes?: number;
  
  /**
   * Warning time before logout in seconds (default: 60)
   */
  warningSeconds?: number;
  
  /**
   * Events that reset the inactivity timer
   */
  resetEvents?: ('mousedown' | 'keydown' | 'scroll' | 'touchstart')[];
  
  /**
   * Callback when warning is shown
   */
  onWarning?: () => void;
  
  /**
   * Callback when session expires
   */
  onSessionExpire?: () => void;
}

/**
 * Hook for managing session timeout with inactivity detection
 * 
 * Usage:
 * ```tsx
 * const { showWarning, timeRemaining } = useSessionTimeout({
 *   timeoutMinutes: 15,
 *   warningSeconds: 60,
 *   onSessionExpire: () => console.log('Session expired!')
 * });
 * 
 * if (showWarning) {
 *   return <SessionTimeoutWarning timeRemaining={timeRemaining} />;
 * }
 * ```
 */
export function useSessionTimeout({
  timeoutMinutes = parseInt(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_MIN || '15'),
  warningSeconds = parseInt(process.env.NEXT_PUBLIC_SESSION_WARNING_SEC || '60'),
  resetEvents = ['mousedown', 'keydown', 'scroll', 'touchstart'],
  onWarning,
  onSessionExpire,
}: UseSessionTimeoutOptions = {}) {
  const router = useRouter();
  
  const timeoutRef = useRef<NodeJS.Timeout>();
  const warningTimeoutRef = useRef<NodeJS.Timeout>();
  const lastActivityRef = useRef<number>(Date.now());
  const debounceMs = parseInt(process.env.NEXT_PUBLIC_ACTIVITY_DEBOUNCE_MS || '5000');
  
  const [showWarning, setShowWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(warningSeconds);

  // Calculate timeouts in milliseconds
  const totalTimeoutMs = timeoutMinutes * 60 * 1000;
  const warningTimeMs = totalTimeoutMs - warningSeconds * 1000;

  /**
   * Reset the inactivity timer
   */
  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();
    setShowWarning(false);
    setTimeRemaining(warningSeconds);

    // Clear existing timeouts
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);

    // Set warning timeout
    warningTimeoutRef.current = setTimeout(() => {
      setShowWarning(true);
      onWarning?.();

      // Count down warning
      let secondsLeft = warningSeconds;
      const countdownInterval = setInterval(() => {
        secondsLeft--;
        setTimeRemaining(secondsLeft);

        if (secondsLeft <= 0) {
          clearInterval(countdownInterval);
        }
      }, 1000);
    }, warningTimeMs);

    // Set logout timeout
    timeoutRef.current = setTimeout(() => {
      // Session expired, logout
      onSessionExpire?.();
      
      // Redirect to login
      router.push('/login?reason=session_expired');
    }, totalTimeoutMs);
  }, [totalTimeoutMs, warningTimeMs, warningSeconds, router, onWarning, onSessionExpire]);

  /**
   * Extend session by clicking "Stay Logged In"
   */
  const extendSession = useCallback(() => {
    resetTimer();
  }, [resetTimer]);

  // Set up event listeners for activity
  useEffect(() => {
    const handleActivity = () => {
      // Only reset if enough time has passed (configurable debounce)
      const timeSinceLastActivity = Date.now() - lastActivityRef.current;
      if (timeSinceLastActivity > debounceMs) {
        resetTimer();
      }
    };

    resetEvents.forEach(event => {
      document.addEventListener(event, handleActivity);
    });

    // Initial timer setup
    resetTimer();

    return () => {
      // Cleanup
      resetEvents.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });

      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    };
  }, [resetTimer, resetEvents, debounceMs]);

  return {
    showWarning,
    timeRemaining,
    extendSession,
  };
}

export default useSessionTimeout;
