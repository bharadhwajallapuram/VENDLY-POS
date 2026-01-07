/**
 * Vendly POS - Real-time Inventory Hook
 * ======================================
 * WebSocket integration for live inventory updates and alerts
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export enum InventoryEventType {
  UPDATED = 'inventory_updated',
  LOW_STOCK = 'inventory_low_stock',
  OUT_OF_STOCK = 'inventory_out_of_stock',
  PRODUCT_CREATED = 'product_created',
  PRODUCT_UPDATED = 'product_updated',
  SYSTEM_NOTIFICATION = 'system_notification',
}

export interface InventoryUpdateData {
  product_id: number;
  product_name: string;
  previous_qty: number;
  new_qty: number;
  change: number;
  reason: string; // 'sale', 'adjustment', 'restock', 'return'
  min_qty: number;
  is_low_stock: boolean;
  is_out_of_stock: boolean;
  warehouse_id?: number;
  updated_at: string;
}

export interface ProductEventData {
  id: number;
  name: string;
  sku?: string;
  barcode?: string;
  quantity: number;
  price: number;
  [key: string]: any;
}

export interface SystemNotification {
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  timestamp?: string;
}

export interface WSMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
}

type InventoryEventHandler = (data: InventoryUpdateData) => void;
type ProductEventHandler = (data: ProductEventData) => void;
type NotificationHandler = (data: SystemNotification) => void;

interface UseInventorySyncOptions {
  enabled?: boolean;
  endpoint?: 'inventory' | 'sales' | 'notifications' | 'all';
  userId?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onInventoryUpdate?: InventoryEventHandler;
  onLowStock?: InventoryEventHandler;
  onOutOfStock?: InventoryEventHandler;
  onProductCreated?: ProductEventHandler;
  onProductUpdated?: ProductEventHandler;
  onNotification?: NotificationHandler;
  onConnectionOpen?: () => void;
  onConnectionClose?: () => void;
  onError?: (error: Error) => void;
}

export function useInventorySync(options: UseInventorySyncOptions = {}) {
  const {
    enabled = true,
    endpoint = 'inventory',
    userId,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onInventoryUpdate,
    onLowStock,
    onOutOfStock,
    onProductCreated,
    onProductUpdated,
    onNotification,
    onConnectionOpen,
    onConnectionClose,
    onError,
  } = options;

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const isCleaningUpRef = useRef(false);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<InventoryUpdateData | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting' | 'error'>('disconnected');

  // Get API URL
  const getApiUrl = useCallback(() => {
    if (typeof window !== 'undefined') {
      // Use the API URL from environment or default to localhost:8000
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      return apiUrl.replace('http', 'ws');
    }
    return 'ws://localhost:8000';
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || !mountedRef.current || isCleaningUpRef.current) return;

    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Also skip if we're already connecting
    if (websocketRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    try {
      setConnectionStatus('connecting');
      const apiUrl = getApiUrl();
      const userParam = userId ? `?user_id=${userId}` : '';
      const wsUrl = `${apiUrl}/api/v1/ws/${endpoint}${userParam}`;

      websocketRef.current = new WebSocket(wsUrl);

      websocketRef.current.onopen = () => {
        if (reconnectAttemptsRef.current === 0) {
          // Only log on first connection, not reconnects
          console.log(`[Inventory Sync] Connected to ${endpoint} WebSocket`);
        }
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
        onConnectionOpen?.();
      };

      websocketRef.current.onmessage = (event: MessageEvent) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('[Inventory Sync] Error parsing message:', error);
          onError?.(new Error('Failed to parse WebSocket message'));
        }
      };

      websocketRef.current.onerror = () => {
        // Don't log errors during cleanup (React Strict Mode double-invocation)
        if (isCleaningUpRef.current || !mountedRef.current) {
          return;
        }
        // Reduce error noise - only log on first error
        if (reconnectAttemptsRef.current === 0) {
          console.warn('[Inventory Sync] WebSocket connection error');
        }
        setConnectionStatus('error');
        onError?.(new Error('WebSocket connection error'));
      };

      websocketRef.current.onclose = () => {
        // Don't update state or reconnect during cleanup
        if (isCleaningUpRef.current || !mountedRef.current) {
          return;
        }
        setIsConnected(false);
        setConnectionStatus('disconnected');
        onConnectionClose?.();

        // Attempt to reconnect with exponential backoff
        if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          // Exponential backoff: 2s, 4s, 8s, 16s, 32s (capped at 30s)
          const backoffDelay = Math.min(
            Math.pow(2, reconnectAttemptsRef.current) * 1000,
            30000
          );
          // Only log reconnect attempts after the first few
          if (reconnectAttemptsRef.current <= 2) {
            console.log(
              `[Inventory Sync] Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
            );
          }
          reconnectTimeoutRef.current = setTimeout(connect, backoffDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error(
            `[Inventory Sync] Max reconnection attempts (${maxReconnectAttempts}) reached. Giving up.`
          );
        }
      };
    } catch (error) {
      console.error('[Inventory Sync] Connection error:', error);
      setConnectionStatus('error');
      onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }, [enabled, endpoint, userId, getApiUrl, reconnectInterval, maxReconnectAttempts, onConnectionOpen, onConnectionClose, onError]);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((message: WSMessage) => {
    const { type, data, timestamp } = message;

    switch (type) {
      case InventoryEventType.UPDATED:
        setLastUpdate(data);
        onInventoryUpdate?.(data);
        break;

      case InventoryEventType.LOW_STOCK:
        setLastUpdate(data);
        onLowStock?.(data);
        console.warn(`[Inventory Sync] Low stock alert: ${data.product_name} (${data.new_qty}/${data.min_qty})`);
        break;

      case InventoryEventType.OUT_OF_STOCK:
        setLastUpdate(data);
        onOutOfStock?.(data);
        console.warn(`[Inventory Sync] Out of stock: ${data.product_name}`);
        break;

      case InventoryEventType.PRODUCT_CREATED:
        onProductCreated?.(data);
        console.log('[Inventory Sync] Product created:', data.name);
        break;

      case InventoryEventType.PRODUCT_UPDATED:
        onProductUpdated?.(data);
        console.log('[Inventory Sync] Product updated:', data.name);
        break;

      case InventoryEventType.SYSTEM_NOTIFICATION:
        onNotification?.(data);
        console.log('[Inventory Sync] Notification:', data.title);
        break;

      default:
        console.debug('[Inventory Sync] Unknown event type:', type);
    }
  }, [onInventoryUpdate, onLowStock, onOutOfStock, onProductCreated, onProductUpdated, onNotification]);

  // Disconnect
  const disconnect = useCallback(() => {
    isCleaningUpRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (websocketRef.current) {
      const ws = websocketRef.current;
      websocketRef.current = null;
      
      // Remove event handlers before closing to prevent error callbacks
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      
      // Close the connection if it's open or connecting
      try {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      } catch {
        // Ignore close errors during cleanup
      }
    }
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  // Setup and cleanup
  useEffect(() => {
    mountedRef.current = true;
    isCleaningUpRef.current = false;
    
    if (enabled) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    isConnected,
    connectionStatus,
    lastUpdate,
    connect,
    disconnect,
  };
}

/**
 * Hook for listening to low-stock alerts
 */
export function useLowStockAlerts(userId?: number) {
  const [lowStockItems, setLowStockItems] = useState<Map<number, InventoryUpdateData>>(new Map());
  const [outOfStockItems, setOutOfStockItems] = useState<Map<number, InventoryUpdateData>>(new Map());

  const { isConnected } = useInventorySync({
    endpoint: 'inventory',
    userId,
    onLowStock: (data) => {
      setLowStockItems((prev) => {
        const updated = new Map(prev);
        updated.set(data.product_id, data);
        return updated;
      });
    },
    onOutOfStock: (data) => {
      setOutOfStockItems((prev) => {
        const updated = new Map(prev);
        updated.set(data.product_id, data);
        return updated;
      });
      // Remove from low stock when out of stock
      setLowStockItems((prev) => {
        const updated = new Map(prev);
        updated.delete(data.product_id);
        return updated;
      });
    },
    onInventoryUpdate: (data) => {
      // Clear from both lists when inventory is restored
      if (!data.is_low_stock && !data.is_out_of_stock) {
        setLowStockItems((prev) => {
          const updated = new Map(prev);
          updated.delete(data.product_id);
          return updated;
        });
        setOutOfStockItems((prev) => {
          const updated = new Map(prev);
          updated.delete(data.product_id);
          return updated;
        });
      }
    },
  });

  return {
    isConnected,
    lowStockItems: Array.from(lowStockItems.values()),
    outOfStockItems: Array.from(outOfStockItems.values()),
    lowStockCount: lowStockItems.size,
    outOfStockCount: outOfStockItems.size,
    totalAlerts: lowStockItems.size + outOfStockItems.size,
  };
}

/**
 * Hook for listening to all product updates
 */
export function useProductUpdates(userId?: number) {
  const [products, setProducts] = useState<Map<number, ProductEventData>>(new Map());

  const { isConnected } = useInventorySync({
    endpoint: 'all',
    userId,
    onProductCreated: (data) => {
      setProducts((prev) => {
        const updated = new Map(prev);
        updated.set(data.id, data);
        return updated;
      });
    },
    onProductUpdated: (data) => {
      setProducts((prev) => {
        const updated = new Map(prev);
        updated.set(data.id, data);
        return updated;
      });
    },
  });

  return {
    isConnected,
    products: Array.from(products.values()),
    productCount: products.size,
  };
}

export default useInventorySync;
