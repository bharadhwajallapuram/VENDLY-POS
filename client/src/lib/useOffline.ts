// ===========================================
// Vendly POS - Offline Mode Hook
// ===========================================
// React hook for managing online/offline status
// and automatic synchronization

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  getQueuedSales,
  getPendingCount,
  queueSale,
  batchSyncSales,
  syncAllSales,
  OfflineSale,
  SyncResult,
} from './offlineQueue';
import { OFFLINE_CONFIG } from '@/config/offlineConfig';

export interface UseOfflineReturn {
  isOnline: boolean;
  pendingCount: number;
  queuedSales: OfflineSale[];
  isSyncing: boolean;
  lastSyncTime: Date | null;
  lastSyncResult: { synced: number; failed: number } | null;
  syncNow: () => Promise<void>;
  queueOfflineSale: typeof queueSale;
}

export function useOffline(): UseOfflineReturn {
  const [isOnline, setIsOnline] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return navigator.onLine;
    }
    return true;
  });
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [queuedSales, setQueuedSales] = useState<OfflineSale[]>([]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<{ synced: number; failed: number } | null>(null);
  
  const syncTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const wasOfflineRef = useRef<boolean>(false);

  // Update queue state
  const refreshQueueState = useCallback(() => {
    setQueuedSales(getQueuedSales());
    setPendingCount(getPendingCount());
  }, []);

  // Sync function
  const syncNow = useCallback(async () => {
    const token = localStorage.getItem('vendly_token');
    if (!token || isSyncing || !isOnline) return;

    const pending = getPendingCount();
    if (pending === 0) return;

    setIsSyncing(true);
    try {
      // Try batch sync first, fallback to individual
      const result = await batchSyncSales(token);
      setLastSyncResult({ synced: result.synced, failed: result.failed });
      setLastSyncTime(new Date());
      refreshQueueState();

      // Show notification for sync result
      if (result.synced > 0 || result.failed > 0) {
        console.log(`Sync complete: ${result.synced} synced, ${result.failed} failed`);
      }
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, isOnline, refreshQueueState]);

  // Handle online status changes
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      
      // If we were offline and now online, sync after a short delay
      if (wasOfflineRef.current) {
        wasOfflineRef.current = false;
        
        // Clear any existing timeout
        if (syncTimeoutRef.current) {
          clearTimeout(syncTimeoutRef.current);
        }
        
        // Wait a bit for connection to stabilize, then sync
        syncTimeoutRef.current = setTimeout(() => {
          syncNow();
        }, OFFLINE_CONFIG.RECONNECTION_DELAY);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
      wasOfflineRef.current = true;
      
      // Clear sync timeout if going offline
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current);
      }
    };

    // Initial state
    refreshQueueState();

    // Listen for network status changes
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Listen for queue changes
    const handleQueueChange = () => {
      refreshQueueState();
    };
    window.addEventListener('offlineQueueChanged', handleQueueChange);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('offlineQueueChanged', handleQueueChange);
      
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current);
      }
    };
  }, [refreshQueueState, syncNow]);

  // Periodic sync when online (every 30 seconds)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!isOnline) return;

    const interval = setInterval(() => {
      if (getPendingCount() > 0 && !isSyncing) {
        syncNow();
      }
    }, OFFLINE_CONFIG.PERIODIC_SYNC_INTERVAL);

    return () => clearInterval(interval);
  }, [isOnline, isSyncing, syncNow]);

  // Initial sync on mount if online and has pending
  useEffect(() => {
    if (isOnline && getPendingCount() > 0) {
      syncNow();
    }
  }, [isOnline, syncNow]);

  return {
    isOnline,
    pendingCount,
    queuedSales,
    isSyncing,
    lastSyncTime,
    lastSyncResult,
    syncNow,
    queueOfflineSale: queueSale,
  };
}
