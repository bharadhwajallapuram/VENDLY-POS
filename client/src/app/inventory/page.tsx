'use client';

// ===========================================
// Vendly POS - Inventory Page
// ===========================================

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useInventorySync, useLowStockAlerts } from '@/hooks/useInventorySync';
import LowStockAlerts from '@/components/LowStockAlerts';
import ReorderModal from '@/components/ReorderModal';
import { API_URL } from '@/lib/api';
import { toastManager } from '@/components/Toast';

interface InventorySummary {
  total_products: number;
  in_stock: number;
  out_of_stock: number;
  low_stock: number;
  total_quantity: number;
  total_value: number;
  timestamp: string;
}

interface LowStockProduct {
  id: number;
  name: string;
  sku?: string;
  current_qty: number;
  min_qty: number;
  shortage: number;
  price: number;
}

interface OutOfStockProduct {
  id: number;
  name: string;
  sku?: string;
  price: number;
}

function InventoryContent() {
  const [summary, setSummary] = useState<InventorySummary | null>(null);
  const [lowStockList, setLowStockList] = useState<LowStockProduct[]>([]);
  const [outOfStockList, setOutOfStockList] = useState<OutOfStockProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  
  // Reorder modal state
  const [showReorderModal, setShowReorderModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<{ id: number; name: string; current_qty: number; min_qty: number } | null>(null);

  const { isConnected: wsConnected } = useInventorySync({
    endpoint: 'inventory',
    onInventoryUpdate: () => {
      // Refresh data when inventory updates
      if (autoRefreshEnabled) {
        refreshData();
      }
    },
    onLowStock: () => {
      refreshData();
    },
    onOutOfStock: () => {
      refreshData();
    },
  });

  // Load summary
  async function loadSummary() {
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/inventory/summary`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (err) {
      console.error('Failed to load inventory summary:', err);
    }
  }

  // Load low stock products
  async function loadLowStockProducts() {
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/inventory/low-stock`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setLowStockList(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load low stock products:', err);
    }
  }

  // Load out of stock products
  async function loadOutOfStockProducts() {
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/inventory/out-of-stock`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setOutOfStockList(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load out of stock products:', err);
    }
  }

  async function refreshData() {
    setLoading(true);
    try {
      await Promise.all([loadSummary(), loadLowStockProducts(), loadOutOfStockProducts()]);
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  }

  // Initial load
  useEffect(() => {
    refreshData();
  }, []);

  const handleAdjustStock = async (productId: number) => {
    const quantity = prompt('Enter quantity to adjust (positive or negative):');
    if (!quantity) return;

    const change = parseInt(quantity, 10);
    if (isNaN(change)) {
      alert('Invalid quantity');
      return;
    }

    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(
        `${API_URL}/api/v1/inventory/adjust/${productId}?quantity_change=${change}&reason=manual_adjustment`,
        {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );

      if (response.ok) {
        await refreshData();
        alert('Inventory adjusted successfully');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to adjust inventory'}`);
      }
    } catch (err) {
      console.error('Failed to adjust inventory:', err);
      alert('Failed to adjust inventory');
    }
  };

  const handleReorder = (product: LowStockProduct | OutOfStockProduct) => {
    const lowStockProduct = lowStockList.find(p => p.id === product.id);
    setSelectedProduct({
      id: product.id,
      name: product.name,
      current_qty: lowStockProduct?.current_qty || 0,
      min_qty: lowStockProduct?.min_qty || 0,
    });
    setShowReorderModal(true);
  };

  const handleReorderSubmit = async (quantity: number, supplierNote: string) => {
    if (!selectedProduct) return;

    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/purchase-orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          product_id: selectedProduct.id,
          quantity,
          supplier_notes: supplierNote,
          status: 'pending',
        }),
      });

      if (response.ok) {
        toastManager.success(`✓ Purchase order created for ${selectedProduct.name}`);
        setShowReorderModal(false);
        setSelectedProduct(null);
        // Optionally refresh data
        await refreshData();
      } else {
        const error = await response.json();
        toastManager.error(`Failed to create order: ${error.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Failed to create purchase order:', err);
      toastManager.error('Failed to create purchase order');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <h1 className="text-2xl font-bold">Inventory Management</h1>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="text-sm text-gray-600 mb-1">Total Products</div>
            <div className="text-3xl font-bold">{summary.total_products}</div>
            <p className="text-xs text-gray-500 mt-1">{summary.total_quantity} units</p>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600 mb-1">In Stock</div>
            <div className="text-3xl font-bold text-green-600">{summary.in_stock}</div>
            <p className="text-xs text-gray-500 mt-1">Ready to sell</p>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600 mb-1">Low Stock</div>
            <div className="text-3xl font-bold text-orange-600">{summary.low_stock}</div>
            <p className="text-xs text-gray-500 mt-1">Need reorder</p>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600 mb-1">Out of Stock</div>
            <div className="text-3xl font-bold text-red-600">{summary.out_of_stock}</div>
            <p className="text-xs text-gray-500 mt-1">Unavailable</p>
          </div>
        </div>
      )}

      {/* Out of Stock Section */}
      {outOfStockList.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-red-600">🔴 Out of Stock ({outOfStockList.length})</h2>
          <div className="bg-red-50 border border-red-200 rounded-lg overflow-hidden">
            {outOfStockList.map((item) => (
              <div key={item.id} className="p-4 border-b border-red-200 last:border-b-0 flex justify-between items-center hover:bg-red-100 transition">
                <div>
                  <p className="font-semibold text-gray-800">{item.name}</p>
                  {item.sku && <p className="text-xs text-gray-500">SKU: {item.sku}</p>}
                  <p className="text-sm text-red-600">Quantity: 0</p>
                </div>
                <button
                  onClick={() => handleReorder(item)}
                  className="px-3 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition"
                >
                  Reorder
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Low Stock Section */}
      {lowStockList.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-orange-600">⚠️ Low Stock ({lowStockList.length})</h2>
          <div className="bg-orange-50 border border-orange-200 rounded-lg overflow-hidden">
            {lowStockList.map((item) => (
              <div key={item.id} className="p-4 border-b border-orange-200 last:border-b-0 flex justify-between items-center hover:bg-orange-100 transition">
                <div>
                  <p className="font-semibold text-gray-800">{item.name}</p>
                  {item.sku && <p className="text-xs text-gray-500">SKU: {item.sku}</p>}
                  <p className="text-sm text-orange-600">
                    Quantity: <strong>{item.current_qty}</strong> / Minimum: <strong>{item.min_qty}</strong> (Shortage: {item.shortage} units)
                  </p>
                </div>
                <button
                  onClick={() => handleReorder(item)}
                  className="px-3 py-2 bg-orange-600 text-white rounded text-sm hover:bg-orange-700 transition"
                >
                  Reorder
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && summary && summary.out_of_stock === 0 && summary.low_stock === 0 && (
        <div className="card bg-green-50 border-green-200">
          <div className="text-center py-8">
            <div className="text-3xl mb-2">✓</div>
            <h3 className="text-lg font-semibold text-green-800">All Stock Levels Healthy</h3>
            <p className="text-green-700">No low stock or out of stock items to manage</p>
          </div>
        </div>
      )}

      {/* Reorder Modal */}
      {selectedProduct && (
        <ReorderModal
          isOpen={showReorderModal}
          productId={selectedProduct.id}
          productName={selectedProduct.name}
          currentStock={selectedProduct.current_qty}
          minStock={selectedProduct.min_qty}
          onClose={() => {
            setShowReorderModal(false);
            setSelectedProduct(null);
          }}
          onSubmit={handleReorderSubmit}
        />
      )}
    </div>
  );
}

export default function InventoryPage() {
  return (
    <ProtectedRoute roles={['manager', 'admin']}>
      <InventoryContent />
    </ProtectedRoute>
  );
}
