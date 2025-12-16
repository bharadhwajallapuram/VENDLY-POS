'use client';

import { useState, useEffect } from 'react';

interface QueueItem {
  id: string;
  synced: boolean;
  syncError?: string;
  retryCount: number;
  items: Array<{
    product_id: number;
    quantity: number;
    unit_price: number;
    discount: number;
  }>;
  customer_id?: number;
  created_at: string;
}

export default function OfflineQueueDebug() {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Access the debug utility
    const debug = (window as any).__vendly_offline_debug;
    if (debug) {
      const queueData = debug.getQueue();
      setQueue(queueData);
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, []);

  const handleClearFailed = () => {
    const debug = (window as any).__vendly_offline_debug;
    if (debug) {
      debug.clearFailedSales();
      const queueData = debug.getQueue();
      setQueue(queueData);
    }
  };

  const handleRemoveSale = (saleId: string) => {
    const debug = (window as any).__vendly_offline_debug;
    if (debug) {
      debug.removeSale(saleId);
      const queueData = debug.getQueue();
      setQueue(queueData);
    }
  };

  const handleClearAll = () => {
    if (confirm('Are you sure you want to clear ALL queued sales?')) {
      const debug = (window as any).__vendly_offline_debug;
      if (debug) {
        debug.clearQueue();
        setQueue([]);
      }
    }
  };

  if (loading) {
    return <div className="p-8">Loading queue...</div>;
  }

  if (!queue.length) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Offline Queue Debug</h1>
        <p className="text-gray-600">No queued sales.</p>
      </div>
    );
  }

  const failedSales = queue.filter(s => s.synced && s.syncError);
  const pendingSales = queue.filter(s => !s.synced && s.retryCount < 3);
  const exceededRetries = queue.filter(s => s.retryCount >= 3);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Offline Queue Debug</h1>

      <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded">
        <h2 className="text-lg font-semibold mb-4">Queue Summary</h2>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Sales</p>
            <p className="text-2xl font-bold">{queue.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Pending</p>
            <p className="text-2xl font-bold text-orange-600">{pendingSales.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Exceeded Retries</p>
            <p className="text-2xl font-bold text-red-600">{exceededRetries.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Failed</p>
            <p className="text-2xl font-bold text-red-600">{failedSales.length}</p>
          </div>
        </div>
      </div>

      <div className="mb-6 flex gap-2">
        {failedSales.length > 0 && (
          <button
            onClick={handleClearFailed}
            className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600"
          >
            Clear Failed Sales ({failedSales.length})
          </button>
        )}
        {queue.length > 0 && (
          <button
            onClick={handleClearAll}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Clear All Sales
          </button>
        )}
      </div>

      <div className="space-y-4">
        {queue.map(sale => (
          <div
            key={sale.id}
            className={`p-4 border rounded ${
              sale.syncError
                ? 'border-red-300 bg-red-50'
                : sale.synced
                  ? 'border-green-300 bg-green-50'
                  : 'border-orange-300 bg-orange-50'
            }`}
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="font-mono text-sm text-gray-700">{sale.id}</p>
                <p className="text-xs text-gray-600 mt-1">
                  Created: {new Date(sale.created_at).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => handleRemoveSale(sale.id)}
                className="px-3 py-1 text-sm bg-red-400 text-white rounded hover:bg-red-500"
              >
                Remove
              </button>
            </div>

            <div className="grid grid-cols-4 gap-2 text-sm mb-2">
              <div>
                <span className="text-gray-600">Status:</span>
                <span className="font-semibold ml-1">
                  {sale.synced ? '✓ Synced' : '○ Pending'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Items:</span>
                <span className="font-semibold ml-1">{sale.items.length}</span>
              </div>
              <div>
                <span className="text-gray-600">Retries:</span>
                <span className={`font-semibold ml-1 ${sale.retryCount >= 3 ? 'text-red-600' : ''}`}>
                  {sale.retryCount}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Customer:</span>
                <span className="font-semibold ml-1">{sale.customer_id || 'None'}</span>
              </div>
            </div>

            {sale.syncError && (
              <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-sm">
                <p className="font-semibold text-red-800">Error:</p>
                <p className="text-red-700 font-mono text-xs mt-1">{sale.syncError}</p>
              </div>
            )}

            <div className="mt-3 text-xs">
              <p className="text-gray-600 font-semibold mb-1">Items:</p>
              <div className="space-y-1 bg-white p-2 rounded border border-gray-200">
                {sale.items.map((item, idx) => (
                  <p key={idx} className="font-mono">
                    Product {item.product_id}: {item.quantity}x @${item.unit_price.toFixed(2)}
                    {item.discount > 0 && ` -$${item.discount.toFixed(2)}`}
                  </p>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
