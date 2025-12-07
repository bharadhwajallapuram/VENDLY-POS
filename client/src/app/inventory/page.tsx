'use client';

// ===========================================
// Vendly POS - Inventory Page
// ===========================================

import ProtectedRoute from '@/components/ProtectedRoute';

function InventoryContent() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Inventory Management</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Total Products</div>
          <div className="text-3xl font-bold">0</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Low Stock Items</div>
          <div className="text-3xl font-bold text-orange-600">0</div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600 mb-1">Out of Stock</div>
          <div className="text-3xl font-bold text-red-600">0</div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Stock Levels</h2>
        <p className="text-gray-500 text-center py-8">
          Inventory tracking coming soon...
        </p>
      </div>
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
