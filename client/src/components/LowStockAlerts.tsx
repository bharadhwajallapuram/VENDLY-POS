'use client';

import { useState, useEffect } from 'react';
import { useLowStockAlerts, InventoryUpdateData } from '@/hooks/useInventorySync';

interface AlertItemProps {
  item: InventoryUpdateData;
  onDismiss?: (productId: number) => void;
  onReorder?: (productId: number) => void;
}

function AlertItem({ item, onDismiss, onReorder }: AlertItemProps) {
  const severity = item.is_out_of_stock ? 'critical' : 'warning';
  const bgColor = severity === 'critical' ? 'bg-red-50' : 'bg-yellow-50';
  const borderColor = severity === 'critical' ? 'border-red-200' : 'border-yellow-200';
  const textColor = severity === 'critical' ? 'text-red-800' : 'text-yellow-800';
  const badgeColor = severity === 'critical' 
    ? 'bg-red-100 text-red-800' 
    : 'bg-yellow-100 text-yellow-800';

  return (
    <div className={`${bgColor} ${borderColor} border rounded-lg p-4 mb-3`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className={`font-semibold ${textColor}`}>
              {item.product_name}
            </h4>
            <span className={`text-xs px-2 py-1 rounded ${badgeColor}`}>
              {severity === 'critical' ? 'OUT OF STOCK' : 'LOW STOCK'}
            </span>
          </div>
          
          <p className={`text-sm ${textColor} mb-2`}>
            Current: <strong>{item.new_qty}</strong> units
            {item.min_qty > 0 && (
              <>
                {' '} | Minimum: <strong>{item.min_qty}</strong> units
                {!item.is_out_of_stock && (
                  <>
                    {' '} | Shortage: <strong>{item.min_qty - item.new_qty}</strong> units
                  </>
                )}
              </>
            )}
          </p>

          <p className={`text-xs ${textColor} opacity-75`}>
            Last updated: {new Date(item.updated_at).toLocaleTimeString()}
          </p>
        </div>

        <div className="flex gap-2 ml-4">
          {onReorder && (
            <button
              onClick={() => onReorder(item.product_id)}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-800 text-white text-sm rounded transition-colors"
            >
              Reorder
            </button>
          )}
          {onDismiss && (
            <button
              onClick={() => onDismiss(item.product_id)}
              className={`px-3 py-1 ${
                severity === 'critical'
                  ? 'bg-red-200 hover:bg-red-300 text-red-800'
                  : 'bg-yellow-200 hover:bg-yellow-300 text-yellow-800'
              } text-sm rounded transition-colors`}
            >
              ✕
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface LowStockAlertsProps {
  userId?: number;
  maxHeight?: string;
  showTitle?: boolean;
  onReorder?: (productId: number) => void;
}

export function LowStockAlerts({
  userId,
  maxHeight = 'max-h-96',
  showTitle = true,
  onReorder,
}: LowStockAlertsProps) {
  const { isConnected, lowStockItems, outOfStockItems, totalAlerts } = useLowStockAlerts(userId);
  const [dismissedItems, setDismissedItems] = useState<Set<number>>(new Set());

  // Filter out dismissed items
  const visibleLowStock = lowStockItems.filter((item) => !dismissedItems.has(item.product_id));
  const visibleOutOfStock = outOfStockItems.filter((item) => !dismissedItems.has(item.product_id));
  const visibleTotal = visibleLowStock.length + visibleOutOfStock.length;

  const handleDismiss = (productId: number) => {
    setDismissedItems((prev) => {
      const updated = new Set(prev);
      updated.add(productId);
      return updated;
    });
  };

  const handleClearAll = () => {
    setDismissedItems(new Set([
      ...visibleLowStock.map(item => item.product_id),
      ...visibleOutOfStock.map(item => item.product_id)
    ]));
  };

  if (visibleTotal === 0) {
    return (
      <div className="card bg-green-50 border-green-200">
        <div className="flex items-center gap-2">
          <div className="text-2xl">✓</div>
          <div>
            <p className="text-green-800 font-semibold">All Stock Levels Good</p>
            <p className="text-sm text-green-700">No low stock or out of stock items</p>
          </div>
        </div>
        {!isConnected && (
          <p className="text-xs text-gray-500 mt-2">
            ⚠️ Real-time updates disconnected - refresh to reconnect
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="card border-orange-200 bg-orange-50">
      {showTitle && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-bold text-orange-900">
              ⚠️ Stock Alerts ({visibleTotal})
            </h3>
            {visibleTotal > 0 && (
              <button
                onClick={handleClearAll}
                className="text-xs text-orange-700 hover:text-orange-900 underline"
              >
                Clear All
              </button>
            )}
          </div>
          {!isConnected && (
            <p className="text-xs text-red-600 mb-2">
              🔴 Real-time updates disconnected - refresh to reconnect
            </p>
          )}
        </div>
      )}

      <div className={`${maxHeight} overflow-y-auto`}>
        {/* Out of Stock Items (shown first) */}
        {visibleOutOfStock.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-red-800 mb-2">
              Out of Stock ({visibleOutOfStock.length})
            </h4>
            {visibleOutOfStock.map((item) => (
              <AlertItem
                key={item.product_id}
                item={item}
                onDismiss={handleDismiss}
                onReorder={onReorder}
              />
            ))}
          </div>
        )}

        {/* Low Stock Items */}
        {visibleLowStock.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-yellow-800 mb-2">
              Low Stock ({visibleLowStock.length})
            </h4>
            {visibleLowStock.map((item) => (
              <AlertItem
                key={item.product_id}
                item={item}
                onDismiss={handleDismiss}
                onReorder={onReorder}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LowStockAlerts;
