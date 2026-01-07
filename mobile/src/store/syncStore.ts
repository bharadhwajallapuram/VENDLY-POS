/**
 * Sync Store - Zustand store for offline sync management
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { apiService } from '../services/api';

interface PendingAction {
  id: string;
  type: 'sale' | 'inventory_update' | 'customer_create' | 'product_update';
  payload: any;
  createdAt: string;
  retryCount: number;
}

interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncAt: string | null;
  pendingActions: PendingAction[];
  syncErrors: string[];

  // Actions
  setOnlineStatus: (isOnline: boolean) => void;
  addPendingAction: (type: PendingAction['type'], payload: any) => void;
  removePendingAction: (id: string) => void;
  syncPendingActions: () => Promise<void>;
  startNetworkListener: () => () => void;
  clearSyncErrors: () => void;
}

const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const useSyncStore = create<SyncState>()(
  persist(
    (set, get) => ({
      isOnline: true,
      isSyncing: false,
      lastSyncAt: null,
      pendingActions: [],
      syncErrors: [],

      setOnlineStatus: (isOnline) => set({ isOnline }),

      addPendingAction: (type, payload) => {
        const action: PendingAction = {
          id: generateId(),
          type,
          payload,
          createdAt: new Date().toISOString(),
          retryCount: 0,
        };

        set((state) => ({
          pendingActions: [...state.pendingActions, action],
        }));

        // Try to sync immediately if online
        const { isOnline } = get();
        if (isOnline) {
          get().syncPendingActions();
        }
      },

      removePendingAction: (id) => {
        set((state) => ({
          pendingActions: state.pendingActions.filter((a) => a.id !== id),
        }));
      },

      syncPendingActions: async () => {
        const { pendingActions, isSyncing, isOnline } = get();

        if (isSyncing || !isOnline || pendingActions.length === 0) {
          return;
        }

        set({ isSyncing: true, syncErrors: [] });

        const errors: string[] = [];
        const successfulIds: string[] = [];

        for (const action of pendingActions) {
          try {
            switch (action.type) {
              case 'sale':
                await apiService.createSale(action.payload);
                break;
              case 'inventory_update':
                await apiService.updateInventory(action.payload);
                break;
              case 'customer_create':
                await apiService.createCustomer(action.payload);
                break;
              case 'product_update':
                await apiService.updateProduct(action.payload);
                break;
            }
            successfulIds.push(action.id);
          } catch (error: any) {
            const errorMessage = `Failed to sync ${action.type}: ${error.message}`;
            errors.push(errorMessage);

            // Increment retry count
            set((state) => ({
              pendingActions: state.pendingActions.map((a) =>
                a.id === action.id ? { ...a, retryCount: a.retryCount + 1 } : a
              ),
            }));

            // Remove after 5 retries
            if (action.retryCount >= 5) {
              successfulIds.push(action.id);
              errors.push(`Action ${action.type} failed after 5 retries - removed from queue`);
            }
          }
        }

        set((state) => ({
          pendingActions: state.pendingActions.filter((a) => !successfulIds.includes(a.id)),
          isSyncing: false,
          lastSyncAt: new Date().toISOString(),
          syncErrors: errors,
        }));
      },

      startNetworkListener: () => {
        const unsubscribe = NetInfo.addEventListener((state) => {
          const wasOffline = !get().isOnline;
          const isNowOnline = state.isConnected === true;

          set({ isOnline: isNowOnline });

          // Auto-sync when coming back online
          if (wasOffline && isNowOnline) {
            get().syncPendingActions();
          }
        });

        return unsubscribe;
      },

      clearSyncErrors: () => set({ syncErrors: [] }),
    }),
    {
      name: 'vendly-sync',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        pendingActions: state.pendingActions,
        lastSyncAt: state.lastSyncAt,
      }),
    }
  )
);
