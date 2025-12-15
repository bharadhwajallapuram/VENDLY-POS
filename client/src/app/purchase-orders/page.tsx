'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { API_URL } from '@/lib/api';
import { toastManager } from '@/components/Toast';

interface PurchaseOrder {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  supplier_notes: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

function PurchaseOrdersContent() {
  const [orders, setOrders] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>(''); // empty = all
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  
  // Received comment modal state
  const [showReceivedModal, setShowReceivedModal] = useState(false);
  const [receivedOrderId, setReceivedOrderId] = useState<number | null>(null);
  const [receivedComment, setReceivedComment] = useState('');
  const [submittingReceived, setSubmittingReceived] = useState(false);

  // Load purchase orders
  useEffect(() => {
    loadOrders();
  }, [filterStatus]);

  async function loadOrders() {
    setLoading(true);
    try {
      const token = localStorage.getItem('vendly_token');
      const url = filterStatus
        ? `${API_URL}/api/v1/purchase-orders?status=${filterStatus}`
        : `${API_URL}/api/v1/purchase-orders`;

      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        const data = await response.json();
        setOrders(data);
      }
    } catch (err) {
      console.error('Failed to load purchase orders:', err);
      toastManager.error('Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  }

  async function updateOrderStatus(orderId: number, newStatus: string) {
    // If marking as received, show modal for comment
    if (newStatus === 'received') {
      setReceivedOrderId(orderId);
      setReceivedComment('');
      setShowReceivedModal(true);
      return;
    }

    // For other statuses, update directly
    try {
      const token = localStorage.getItem('vendly_token');
      const response = await fetch(`${API_URL}/api/v1/purchase-orders/${orderId}?status=${newStatus}`, {
        method: 'PATCH',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        toastManager.success(`✓ Order status updated to "${newStatus}"`);
        await loadOrders();
      } else {
        const error = await response.json();
        toastManager.error(`Failed: ${error.detail || 'Could not update order'}`);
      }
    } catch (err) {
      console.error('Failed to update order:', err);
      toastManager.error('Failed to update order');
    }
  }

  async function submitReceivedOrder() {
    if (!receivedOrderId) return;

    setSubmittingReceived(true);
    try {
      const token = localStorage.getItem('vendly_token');
      
      // First, update the order status to received
      const response = await fetch(`${API_URL}/api/v1/purchase-orders/${receivedOrderId}?status=received`, {
        method: 'PATCH',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (response.ok) {
        // TODO: Send comment to supplier (implement when backend supports it)
        toastManager.success(`✓ Order marked as received. ${receivedComment ? 'Comment saved.' : ''}`);
        setShowReceivedModal(false);
        setReceivedOrderId(null);
        setReceivedComment('');
        await loadOrders();
      } else {
        const error = await response.json();
        toastManager.error(`Failed: ${error.detail || 'Could not update order'}`);
      }
    } catch (err) {
      console.error('Failed to update order:', err);
      toastManager.error('Failed to update order');
    } finally {
      setSubmittingReceived(false);
    }
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    ordered: 'bg-gray-100 text-gray-800',
    received: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  const statusOptions = ['pending', 'ordered', 'received', 'cancelled'];

  // Define valid next states for each status
  const nextStates: Record<string, string[]> = {
    pending: ['ordered', 'cancelled'],
    ordered: ['received', 'cancelled'],
    received: [], // terminal state
    cancelled: [], // terminal state
  };

  function getAvailableTransitions(currentStatus: string): string[] {
    return nextStates[currentStatus] || [];
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <h1 className="text-2xl font-bold">Purchase Orders</h1>

      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex gap-2">
          <button
            onClick={() => setFilterStatus('')}
            className={`px-4 py-2 rounded text-sm font-medium transition ${
              filterStatus === ''
                ? 'bg-gray-800 text-white'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            All
          </button>
          {statusOptions.map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-4 py-2 rounded text-sm font-medium transition capitalize ${
                filterStatus === status
                  ? 'bg-gray-800 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Orders List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : orders.length === 0 ? (
        <div className="card bg-gray-50 border-gray-200">
          <div className="text-center py-8">
            <div className="text-3xl mb-2">📦</div>
            <h3 className="text-lg font-semibold text-gray-800">No Purchase Orders</h3>
            <p className="text-gray-700">Create a new purchase order from the Inventory page</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <div key={order.id} className="card border-l-4 border-l-gray-800 hover:shadow-lg transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{order.product_name}</h3>
                    <span className={`text-xs px-2 py-1 rounded font-medium capitalize ${statusColors[order.status] || 'bg-gray-100 text-gray-800'}`}>
                      {order.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-600">Order ID</p>
                      <p className="text-sm font-mono font-semibold">#{order.id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Quantity</p>
                      <p className="text-lg font-bold text-gray-900">{order.quantity} units</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Ordered</p>
                      <p className="text-sm">{new Date(order.created_at).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Last Updated</p>
                      <p className="text-sm">{new Date(order.updated_at).toLocaleDateString()}</p>
                    </div>
                  </div>

                  {order.supplier_notes && (
                    <div className="bg-gray-50 rounded p-2 mb-3">
                      <p className="text-xs text-gray-600 font-medium">Supplier Notes</p>
                      <p className="text-sm text-gray-700">{order.supplier_notes}</p>
                    </div>
                  )}
                </div>

                {/* Status Actions */}
                <div className="ml-4">
                  <div className="flex flex-col gap-2">
                    {getAvailableTransitions(order.status).length === 0 ? (
                      <div className="px-3 py-1 text-xs font-medium text-gray-500 text-center">
                        No transitions
                      </div>
                    ) : (
                      getAvailableTransitions(order.status).map((status) => (
                        <button
                          key={status}
                          onClick={() => updateOrderStatus(order.id, status)}
                          className={`px-3 py-2 text-xs font-medium rounded transition capitalize whitespace-nowrap ${
                            status === 'received'
                              ? 'bg-green-600 hover:bg-green-700 text-white'
                              : status === 'cancelled'
                              ? 'bg-red-600 hover:bg-red-700 text-white'
                              : status === 'ordered'
                              ? 'bg-gray-700 hover:bg-gray-800 text-white'
                              : 'bg-gray-600 hover:bg-gray-700 text-white'
                          }`}
                        >
                          Mark {status}
                        </button>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Received Comment Modal */}
      {showReceivedModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Order Received</h2>
              <p className="text-sm text-gray-600 mt-1">Add a message for the supplier (optional)</p>
            </div>

            <div className="p-6 space-y-4">
              <textarea
                value={receivedComment}
                onChange={(e) => setReceivedComment(e.target.value)}
                placeholder="e.g., 'Items received in good condition', 'Missing packaging', 'Quantity verified', etc."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-600 resize-none"
                rows={4}
              />
              <p className="text-xs text-gray-500">
                This message will be logged with the order for supplier reference
              </p>
            </div>

            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowReceivedModal(false);
                  setReceivedOrderId(null);
                  setReceivedComment('');
                }}
                disabled={submittingReceived}
                className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-200 disabled:text-gray-500 rounded-lg font-medium transition"
              >
                Cancel
              </button>
              <button
                onClick={submitReceivedOrder}
                disabled={submittingReceived}
                className="px-4 py-2 text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-lg font-medium transition"
              >
                {submittingReceived ? 'Submitting...' : 'Confirm Received'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PurchaseOrdersPage() {
  return (
    <ProtectedRoute roles={['manager', 'admin']}>
      <PurchaseOrdersContent />
    </ProtectedRoute>
  );
}
