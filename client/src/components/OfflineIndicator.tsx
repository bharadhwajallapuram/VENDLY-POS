// ===========================================
// Vendly POS - Offline Indicator Component
// ===========================================
// Visual indicator showing online/offline status
// and pending sync count

'use client';

import { useOffline } from '@/lib/useOffline';
import { getQueuedSales } from '@/lib/offlineQueue';
import { useState } from 'react';

interface OfflineIndicatorProps {
  showDetails?: boolean;
}

export default function OfflineIndicator({ showDetails = true }: OfflineIndicatorProps) {
  const { isOnline, pendingCount, isSyncing, syncNow, lastSyncTime, lastSyncResult } = useOffline();
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  
  // Get failed sales with error messages
  const failedSales = getQueuedSales().filter(s => s.syncError);

  // Show only a small dot indicator
  if (!showDetails) {
    return (
      <div
        className={`w-2 h-2 rounded-full ${
          isOnline ? 'bg-green-500' : 'bg-red-500'
        } ${isSyncing ? 'animate-pulse' : ''}`}
        title={isOnline ? 'Online' : 'Offline'}
      />
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isOnline ? 'bg-green-500' : 'bg-red-500'
            } ${isSyncing ? 'animate-pulse' : ''}`}
            title={isOnline ? 'Online' : 'Offline'}
          />
          <span className={`text-sm font-medium ${isOnline ? 'text-green-700' : 'text-red-700'}`}>
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* Pending Count Badge */}
        {pendingCount > 0 && (
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center justify-center px-2 py-1 text-xs font-bold rounded-full ${
                isOnline ? 'bg-yellow-100 text-yellow-800' : 'bg-orange-100 text-orange-800'
              }`}
              title={`${pendingCount} sale(s) pending sync`}
            >
              {pendingCount} pending
            </span>
            
            {/* Sync Button */}
            {isOnline && (
              <button
                onClick={() => syncNow()}
                disabled={isSyncing}
                className={`text-xs px-2 py-1 rounded ${
                  isSyncing
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title="Sync pending sales now"
              >
                {isSyncing ? (
                  <span className="flex items-center gap-1">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Syncing...
                  </span>
                ) : (
                  '🔄 Sync'
                )}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Detailed Status (optional) */}
      {showDetails && lastSyncResult && lastSyncTime && (
        <div className="text-xs text-gray-500 ml-2">
          Last sync: {lastSyncResult.synced} synced, {lastSyncResult.failed} failed
          <span className="ml-1">
            ({new Date(lastSyncTime).toLocaleTimeString()})
          </span>
        </div>
      )}

      {/* Error Details */}
      {failedSales.length > 0 && (
        <div className="ml-2">
          <button
            onClick={() => setShowErrorDetails(!showErrorDetails)}
            className="text-xs text-red-600 hover:text-red-800 underline"
          >
            {showErrorDetails ? 'Hide' : 'Show'} {failedSales.length} failed sale error(s)
          </button>
          
          {showErrorDetails && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
              {failedSales.map((sale, idx) => (
                <div key={sale.id} className="mb-2 pb-2 border-b border-red-200 last:border-b-0">
                  <div className="font-mono text-red-700">
                    <strong>Sale #{idx + 1}:</strong> {sale.syncError}
                  </div>
                  <div className="text-gray-600 text-xs mt-1">
                    Attempts: {sale.retryCount}/{3} | Items: {sale.items.length}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Compact version for navbar
export function OfflineIndicatorCompact() {
  const { isOnline, pendingCount, isSyncing } = useOffline();

  if (isOnline && pendingCount === 0) {
    return null; // Don't show anything when online with no pending
  }

  return (
    <div className="flex items-center gap-1">
      <div
        className={`w-2 h-2 rounded-full ${
          isOnline ? 'bg-green-500' : 'bg-red-500'
        } ${isSyncing ? 'animate-pulse' : ''}`}
      />
      {pendingCount > 0 && (
        <span
          className={`text-xs font-bold ${
            isOnline ? 'text-yellow-600' : 'text-orange-600'
          }`}
        >
          {pendingCount}
        </span>
      )}
    </div>
  );
}

// Offline Banner - shows at top of page when offline
export function OfflineBanner() {
  const { isOnline, pendingCount, isSyncing, syncNow } = useOffline();

  if (isOnline && pendingCount === 0) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 px-4 py-2 text-center text-sm font-medium ${
        isOnline
          ? 'bg-yellow-100 text-yellow-800 border-b border-yellow-200'
          : 'bg-red-100 text-red-800 border-b border-red-200'
      }`}
    >
      {!isOnline ? (
        <span>
          📡 You&apos;re offline. Sales will be saved locally and synced when reconnected.
          {pendingCount > 0 && ` (${pendingCount} pending)`}
        </span>
      ) : (
        <span className="flex items-center justify-center gap-2">
          <span>🔄 {pendingCount} sale(s) pending sync.</span>
          <button
            onClick={() => syncNow()}
            disabled={isSyncing}
            className={`px-2 py-0.5 rounded text-xs ${
              isSyncing
                ? 'bg-gray-200 cursor-not-allowed'
                : 'bg-yellow-200 hover:bg-yellow-300'
            }`}
          >
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </button>
        </span>
      )}
    </div>
  );
}
