// ===========================================
// Vendly POS - Offline Queue Service
// ===========================================
// Manages queuing sales transactions when offline
// and syncing them when back online

import { API_URL } from './api';
import { OFFLINE_CONFIG } from '@/config/offlineConfig';

// Types for offline sales
export interface OfflineSaleItem {
  product_id: number;
  quantity: number;
  unit_price: number;
  discount: number;
}

export interface OfflinePayment {
  method: string;
  amount: number;
}

export interface OfflineSale {
  id: string; // UUID for local tracking
  items: OfflineSaleItem[];
  payments: OfflinePayment[];
  discount: number;
  coupon_code?: string;
  notes?: string;
  customer_id?: number;
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  created_at: string;
  synced: boolean;
  syncError?: string;
  retryCount: number;
}

export interface SyncResult {
  success: boolean;
  offlineId: string;
  serverId?: number;
  error?: string;
}

// Generate a UUID for offline sale tracking
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// Get all queued sales from localStorage
export function getQueuedSales(): OfflineSale[] {
  if (typeof window === 'undefined') return [];
  try {
    const data = localStorage.getItem(OFFLINE_CONFIG.QUEUE_STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Failed to read offline queue:', error);
    return [];
  }
}

// Save queue to localStorage
function saveQueue(sales: OfflineSale[]): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(OFFLINE_CONFIG.QUEUE_STORAGE_KEY, JSON.stringify(sales));
  } catch (error) {
    console.error('Failed to save offline queue:', error);
  }
}

// Add a sale to the offline queue
export function queueSale(sale: Omit<OfflineSale, 'id' | 'created_at' | 'synced' | 'retryCount'>): OfflineSale {
  const offlineSale: OfflineSale = {
    ...sale,
    id: generateUUID(),
    created_at: new Date().toISOString(),
    synced: false,
    retryCount: 0,
  };
  
  const queue = getQueuedSales();
  queue.push(offlineSale);
  saveQueue(queue);
  
  // Dispatch custom event for UI updates
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('offlineQueueChanged', { detail: { queue } }));
  }
  
  return offlineSale;
}

// Remove a sale from the queue
export function removeSale(id: string): void {
  const queue = getQueuedSales();
  const filtered = queue.filter(sale => sale.id !== id);
  saveQueue(filtered);
  
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('offlineQueueChanged', { detail: { queue: filtered } }));
  }
}

// Update a sale in the queue
export function updateSale(id: string, updates: Partial<OfflineSale>): void {
  const queue = getQueuedSales();
  const index = queue.findIndex(sale => sale.id === id);
  if (index !== -1) {
    queue[index] = { ...queue[index], ...updates };
    saveQueue(queue);
    
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('offlineQueueChanged', { detail: { queue } }));
    }
  }
}

// Get count of pending (unsynced) sales
export function getPendingCount(): number {
  return getQueuedSales().filter(sale => !sale.synced).length;
}

// Clear all synced sales from the queue
export function clearSyncedSales(): void {
  const queue = getQueuedSales();
  const pending = queue.filter(sale => !sale.synced);
  saveQueue(pending);
  
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('offlineQueueChanged', { detail: { queue: pending } }));
  }
}

// Clear entire queue (use with caution)
export function clearQueue(): void {
  saveQueue([]);
  
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('offlineQueueChanged', { detail: { queue: [] } }));
  }
}

// Sync a single sale to the server
async function syncSingleSale(sale: OfflineSale, token: string): Promise<SyncResult> {
  try {
    // First, create customer if needed
    let customerId = sale.customer_id;
    if (!customerId && (sale.customer_name || sale.customer_phone || sale.customer_email)) {
      try {
        const customerRes = await fetch(`${API_URL}/api/v1/customers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: sale.customer_name || 'Guest',
            phone: sale.customer_phone || null,
            email: sale.customer_email || null,
          }),
        });
        if (customerRes.ok) {
          const customerData = await customerRes.json();
          customerId = customerData.id;
        }
      } catch (e) {
        console.error('Failed to create customer during sync:', e);
      }
    }

    // Create the sale
    const salePayload = {
      items: sale.items,
      payments: sale.payments,
      discount: sale.discount,
      coupon_code: sale.coupon_code || undefined,
      notes: sale.notes ? `${sale.notes} [Offline Sale: ${sale.created_at}]` : `[Offline Sale: ${sale.created_at}]`,
      customer_id: customerId,
    };

    const response = await fetch(`${API_URL}/api/v1/sales`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(salePayload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Sync failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const serverSale = await response.json();
    return {
      success: true,
      offlineId: sale.id,
      serverId: serverSale.id,
    };
  } catch (error) {
    return {
      success: false,
      offlineId: sale.id,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

// Sync all pending sales to the server
export async function syncAllSales(token: string): Promise<{
  synced: number;
  failed: number;
  results: SyncResult[];
}> {
  const queue = getQueuedSales();
  // Only filter out sales that are already synced. Don't limit retries - keep trying.
  const pending = queue.filter(sale => !sale.synced);
  
  const results: SyncResult[] = [];
  let synced = 0;
  let failed = 0;

  for (const sale of pending) {
    const result = await syncSingleSale(sale, token);
    results.push(result);
    
    if (result.success) {
      updateSale(sale.id, { synced: true, syncError: undefined });
      synced++;
    } else {
      updateSale(sale.id, { 
        retryCount: sale.retryCount + 1,
        syncError: result.error,
      });
      failed++;
    }
  }

  // Clean up synced sales
  clearSyncedSales();

  return { synced, failed, results };
}

// Batch sync endpoint (more efficient for multiple sales)
export async function batchSyncSales(token: string): Promise<{
  synced: number;
  failed: number;
  results: SyncResult[];
}> {
  const queue = getQueuedSales();
  console.log('[Batch Sync] Total queued sales:', queue.length);
  console.log('[Batch Sync] Queue contents:', queue);
  
  // Log detailed info about why each sale is filtered
  queue.forEach((sale, idx) => {
    console.log(`[Batch Sync] Sale ${idx}: id=${sale.id}, synced=${sale.synced}, retryCount=${sale.retryCount}, maxRetries=${OFFLINE_CONFIG.MAX_RETRIES}`);
  });
  
  // Only filter out sales that are already synced. Don't limit retries - keep trying.
  const pending = queue.filter(sale => !sale.synced);
  console.log('[Batch Sync] Pending sales:', pending.length, pending);
  
  if (pending.length === 0) {
    console.log('[Batch Sync] No pending sales to sync');
    return { synced: 0, failed: 0, results: [] };
  }

  try {
    // Try batch endpoint first
    console.log('[Batch Sync] Calling batch-sync endpoint with', pending.length, 'sales');
    const response = await fetch(`${API_URL}/api/v1/sales/batch-sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ sales: pending }),
    });

    console.log('[Batch Sync] Response status:', response.status);
    if (response.ok) {
      const data = await response.json();
      console.log('[Batch Sync] Response data:', data);
      
      // Process results
      const results: SyncResult[] = data.results || [];
      let synced = 0;
      let failed = 0;

      for (const result of results) {
        if (result.success) {
          updateSale(result.offlineId, { synced: true, syncError: undefined });
          synced++;
        } else {
          const sale = pending.find(s => s.id === result.offlineId);
          if (sale) {
            updateSale(result.offlineId, { 
              retryCount: sale.retryCount + 1,
              syncError: result.error,
            });
          }
          failed++;
        }
      }

      clearSyncedSales();
      return { synced, failed, results };
    }
    
    // If batch endpoint fails, fall back to individual sync
    console.warn('Batch sync failed, falling back to individual sync');
    return syncAllSales(token);
  } catch (error) {
    // Fall back to individual sync on network error
    console.warn('Batch sync error, falling back to individual sync:', error);
    return syncAllSales(token);
  }
}

// Debug utility - expose to window for console access
if (typeof window !== 'undefined') {
  (window as any).__vendly_offline_debug = {
    getQueue: getQueuedSales,
    clearQueue,
    getPendingCount,
    removeAll: clearQueue,
  };
}

