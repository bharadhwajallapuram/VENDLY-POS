/**
 * Session Timeout Warning Component
 * Displayed when user is about to be logged out
 */

'use client';

import React from 'react';

interface SessionTimeoutWarningProps {
  /**
   * Seconds remaining before logout
   */
  timeRemaining: number;
  
  /**
   * Callback when user clicks "Stay Logged In"
   */
  onExtend: () => void;
  
  /**
   * Callback when user clicks "Logout"
   */
  onLogout: () => void;
}

export function SessionTimeoutWarning({
  timeRemaining,
  onExtend,
  onLogout,
}: SessionTimeoutWarningProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0">
            <svg
              className="h-6 w-6 text-yellow-600 animate-pulse"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900">
            Session Timeout Warning
          </h2>
        </div>

        {/* Message */}
        <div className="mb-6">
          <p className="text-gray-600 mb-2">
            Your session will expire due to inactivity in:
          </p>
          
          {/* Countdown Timer */}
          <div className="text-center py-4 bg-gray-50 rounded-lg">
            <div className="text-4xl font-bold text-red-600 font-mono">
              {String(Math.floor(timeRemaining / 60)).padStart(2, '0')}:
              {String(timeRemaining % 60).padStart(2, '0')}
            </div>
            <p className="text-sm text-gray-600 mt-2">seconds remaining</p>
          </div>

          <p className="text-sm text-gray-600 mt-4">
            Click &quot;Stay Logged In&quot; to continue working, or your session will be 
            automatically terminated for security.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          {/* Logout Button */}
          <button
            onClick={onLogout}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-colors"
          >
            Logout
          </button>

          {/* Stay Logged In Button */}
          <button
            onClick={onExtend}
            className="flex-1 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Stay Logged In
          </button>
        </div>

        {/* Info Footer */}
        <p className="text-xs text-gray-500 text-center mt-4">
          For security, sessions automatically expire after periods of inactivity
        </p>
      </div>
    </div>
  );
}

export default SessionTimeoutWarning;
