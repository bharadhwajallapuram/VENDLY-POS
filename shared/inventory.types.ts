/**
 * Vendly POS - Inventory Types
 * ============================
 * TypeScript type definitions for inventory system
 */

// ===== Inventory Events =====

export enum InventoryEventType {
  INVENTORY_UPDATED = 'inventory_updated',
  INVENTORY_LOW_STOCK = 'inventory_low_stock',
  INVENTORY_OUT_OF_STOCK = 'inventory_out_of_stock',
  PRODUCT_CREATED = 'product_created',
  PRODUCT_UPDATED = 'product_updated',
  SYSTEM_NOTIFICATION = 'system_notification',
}

export interface InventoryUpdate {
  product_id: number;
  product_name: string;
  sku?: string;
  barcode?: string;
  previous_qty: number;
  new_qty: number;
  change: number;
  reason: 'sale' | 'adjustment' | 'restock' | 'return' | 'stock_count';
  min_qty: number;
  is_low_stock: boolean;
  is_out_of_stock: boolean;
  warehouse_id?: number;
  updated_at: string;
}

// ===== Inventory Summary =====

export interface InventorySummary {
  total_products: number;
  in_stock: number;
  out_of_stock: number;
  low_stock: number;
  total_quantity: number;
  total_value: number;
  timestamp: string;
}

// ===== Product Stock =====

export interface ProductStock {
  id: number;
  name: string;
  sku?: string;
  barcode?: string;
  quantity: number;
  min_quantity: number;
  price: number;
  cost?: number;
  category_id?: number;
  updated_at: string;
}

export interface LowStockProduct extends ProductStock {
  shortage: number;
  is_low_stock: true;
  is_out_of_stock: false;
}

export interface OutOfStockProduct extends ProductStock {
  is_out_of_stock: true;
  is_low_stock: false;
}

// ===== Inventory Adjustment =====

export interface InventoryAdjustment {
  product_id: number;
  quantity_change: number;
  reason: 'sale' | 'adjustment' | 'restock' | 'return' | 'stock_count';
  notes?: string;
}

export interface InventoryAdjustmentResult {
  id: number;
  name: string;
  quantity: number;
  min_quantity: number;
  change: number;
  reason: string;
  timestamp: string;
}

// ===== Inventory History =====

export interface InventoryHistoryEntry {
  id: number;
  product_id: number;
  product_name: string;
  previous_qty: number;
  new_qty: number;
  change: number;
  reason: string;
  created_by?: number;
  created_by_name?: string;
  notes?: string;
  created_at: string;
}

export interface InventoryHistory {
  product_id: number;
  product_name: string;
  days: number;
  count: number;
  items: InventoryHistoryEntry[];
}

// ===== Alert Configuration =====

export interface AlertConfig {
  low_stock_threshold?: number;
  out_of_stock_alert: boolean;
  low_stock_alert: boolean;
  daily_report_email: boolean;
  notification_channels: Array<'in_app' | 'email' | 'sms' | 'push'>;
}

// ===== Inventory Report =====

export interface InventoryReport {
  period: {
    start_date: string;
    end_date: string;
  };
  summary: InventorySummary;
  low_stock_items: LowStockProduct[];
  out_of_stock_items: OutOfStockProduct[];
  top_movers: Array<{
    product_id: number;
    product_name: string;
    quantity_sold: number;
    revenue: number;
  }>;
  slowest_movers: Array<{
    product_id: number;
    product_name: string;
    quantity_sold: number;
    days_in_inventory: number;
  }>;
  generated_at: string;
}

// ===== WebSocket Messages =====

export interface WSInventoryMessage {
  type: InventoryEventType;
  data: InventoryUpdate;
  timestamp: string;
}

// ===== Reorder =====

export interface ReorderRequest {
  product_id: number;
  quantity: number;
  supplier_id?: number;
  notes?: string;
  urgency: 'normal' | 'high' | 'critical';
}

export interface ReorderSuggestion {
  product_id: number;
  product_name: string;
  current_qty: number;
  recommended_qty: number;
  reorder_point: number;
  lead_time_days: number;
  estimated_cost: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  reason: string;
}

// ===== Bulk Operations =====

export interface BulkInventoryUpdate {
  product_id: number;
  new_quantity: number;
  reason?: string;
}

export interface BulkInventoryUpdateResult {
  successful: number;
  failed: number;
  errors: Array<{
    product_id: number;
    error: string;
  }>;
}

// ===== Stock Count =====

export interface StockCountItem {
  product_id: number;
  counted_quantity: number;
  location?: string;
  counted_by?: string;
  notes?: string;
}

export interface StockCountResult {
  product_id: number;
  product_name: string;
  system_qty: number;
  counted_qty: number;
  variance: number;
  variance_percent: number;
  adjustment_needed: number;
}

// ===== Warehouse (Future) =====

export interface WarehouseStock {
  warehouse_id: number;
  warehouse_name: string;
  product_id: number;
  quantity: number;
  updated_at: string;
}

// ===== Hook State =====

export interface UseInventorySyncState {
  isConnected: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting' | 'error';
  lastUpdate: InventoryUpdate | null;
  error?: Error;
}

export interface UseLowStockAlertsState {
  isConnected: boolean;
  lowStockItems: InventoryUpdate[];
  outOfStockItems: InventoryUpdate[];
  lowStockCount: number;
  outOfStockCount: number;
  totalAlerts: number;
}

// ===== Component Props =====

export interface LowStockAlertsProps {
  userId?: number;
  maxHeight?: string;
  showTitle?: boolean;
  onReorder?: (productId: number) => void;
  onDismiss?: (productId: number) => void;
}

export interface InventoryStatusProps {
  product: ProductStock;
  showPrice?: boolean;
  showHistory?: boolean;
  onAdjust?: (productId: number) => void;
}

export interface InventoryTableProps {
  products: ProductStock[];
  loading?: boolean;
  onSelect?: (productId: number) => void;
  onAdjust?: (productId: number) => void;
  onReorder?: (productId: number) => void;
}
