'use client';

// ===========================================
// Vendly POS - Transactions History Page
// ===========================================

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/store/auth';
import { API_URL, createWebSocket } from '@/lib/api';

interface SaleItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total: number;
}

interface Transaction {
  id: number;
  user_id: number;
  customer_id: number | null;
  subtotal: number;
  tax: number;
  discount: number;
  total: number;
  payment_method: string;
  payment_reference: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  items: SaleItem[];
}

// Helper to format date as YYYY-MM-DD in local timezone
const formatLocalDate = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

function TransactionsContent() {
  const { token } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [showModal, setShowModal] = useState(false);
  // Default to last 7 days to avoid timezone issues
  const [dateRange, setDateRange] = useState(() => {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(today.getDate() - 7);
    return { start: formatLocalDate(weekAgo), end: formatLocalDate(today) };
  });
  const [sortField, setSortField] = useState<'id' | 'created_at' | 'total'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const loadTransactions = useCallback(async (showSpinner = true) => {
    if (!token) return;
    if (showSpinner) setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', '200');
      
      const response = await fetch(`${API_URL}/api/v1/sales?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch transactions');
      
      let data: Transaction[] = await response.json();
      
      // Filter by date range on client side
      // Server now stores EST timestamps
      if (dateRange.start || dateRange.end) {
        data = data.filter(t => {
          const txDate = t.created_at.split('T')[0]; // Get YYYY-MM-DD part
          if (dateRange.start && txDate < dateRange.start) return false;
          if (dateRange.end && txDate > dateRange.end) return false;
          return true;
        });
      }
      
      // Sort by date (newest first)
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      
      setTransactions(data);
      setIsInitialLoad(false);
    } catch (err) {
      console.error('Failed to load transactions:', err);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [dateRange.start, dateRange.end, token]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  // Auto-refresh every 30 seconds as a fallback (silent refresh, no spinner)
  useEffect(() => {
    const interval = setInterval(() => {
      loadTransactions(false); // Don't show spinner on background refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, [loadTransactions]);

  // WebSocket for instant real-time transaction updates
  useEffect(() => {
    const ws = createWebSocket((data: unknown) => {
      const message = data as { event?: string; type?: string; data?: Transaction };
      
      // Check for sale_created event
      if (message.event === 'sale_created' || message.type === 'sale_created') {
        const newTransaction = message.data;
        if (newTransaction) {
          console.log('📥 Real-time transaction received:', newTransaction.id, newTransaction);
          
          // Always add new transactions - let the filter handle display
          setTransactions(prev => {
            // Avoid duplicates
            if (prev.some(t => t.id === newTransaction.id)) {
              console.log('📥 Transaction already exists, skipping');
              return prev;
            }
            console.log('📥 Adding transaction to list');
            // Add to beginning (newest first)
            return [newTransaction, ...prev];
          });
        }
      }
    });

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const filteredTransactions = [...transactions]
    .sort((a, b) => {
      let comparison = 0;
      if (sortField === 'id') {
        comparison = a.id - b.id;
      } else if (sortField === 'created_at') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortField === 'total') {
        comparison = (a.total ?? 0) - (b.total ?? 0);
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const handleSort = (field: 'id' | 'created_at' | 'total') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const SortIcon = ({ field }: { field: 'id' | 'created_at' | 'total' }) => {
    if (sortField !== field) return <span className="text-gray-300 ml-1">↕</span>;
    return <span className="text-sky-500 ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-red-100 text-red-800',
      refunded: 'bg-orange-100 text-orange-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getPaymentIcon = (method: string) => {
    switch (method.toLowerCase()) {
      case 'cash': return '💵';
      case 'card': return '💳';
      case 'digital': return '📱';
      default: return '💰';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const openTransactionDetails = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setShowModal(true);
  };

  // Quick date range presets
  const setDatePreset = (preset: 'today' | 'yesterday' | 'week' | 'month') => {
    const today = new Date();
    let start: Date;
    let end: Date = today;
    
    switch (preset) {
      case 'today':
        start = today;
        break;
      case 'yesterday':
        start = new Date(today);
        start.setDate(today.getDate() - 1);
        end = start;
        break;
      case 'week':
        start = new Date(today);
        start.setDate(today.getDate() - 7);
        break;
      case 'month':
        start = new Date(today);
        start.setMonth(today.getMonth() - 1);
        break;
    }
    
    setDateRange({
      start: formatLocalDate(start),
      end: formatLocalDate(end),
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-500 text-sm mt-1">
            {dateRange.start === dateRange.end 
              ? dateRange.start 
              : `${dateRange.start} to ${dateRange.end}`} ({filteredTransactions.length} results)
          </p>
        </div>
        <div className="flex gap-2 items-center flex-nowrap">
          {/* Quick Presets */}
          <button 
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              dateRange.start === formatLocalDate(new Date()) && dateRange.end === formatLocalDate(new Date())
                ? 'bg-sky-500 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            onClick={() => setDatePreset('today')}
          >
            Today
          </button>
          <button 
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors whitespace-nowrap"
            onClick={() => setDatePreset('yesterday')}
          >
            Yesterday
          </button>
          <button 
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors whitespace-nowrap"
            onClick={() => setDatePreset('week')}
          >
            7 Days
          </button>
          <button 
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors whitespace-nowrap"
            onClick={() => setDatePreset('month')}
          >
            30 Days
          </button>
          <div className="flex items-center gap-1 border border-gray-200 rounded-lg px-2 py-1 bg-white">
            <input
              type="date"
              className="border-0 p-0 text-sm w-28 focus:ring-0"
              value={dateRange.start}
              onChange={(e) => setDateRange((r) => ({ ...r, start: e.target.value }))}
            />
            <span className="text-gray-400">—</span>
            <input
              type="date"
              className="border-0 p-0 text-sm w-28 focus:ring-0"
              value={dateRange.end}
              onChange={(e) => setDateRange((r) => ({ ...r, end: e.target.value }))}
            />
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {loading && isInitialLoad ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-500"></div>
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-lg font-medium">No transactions found</p>
            <p className="text-sm">Try adjusting your date range or filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th 
                    className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors w-16"
                    onClick={() => handleSort('id')}
                  >
                    ID <SortIcon field="id" />
                  </th>
                  <th 
                    className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors w-20"
                    onClick={() => handleSort('created_at')}
                  >
                    Time <SortIcon field="created_at" />
                  </th>
                  <th className="text-center py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-16">Items</th>
                  <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Payment</th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Subtotal</th>
                  <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Tax</th>
                  <th 
                    className="text-right py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors w-24"
                    onClick={() => handleSort('total')}
                  >
                    Total <SortIcon field="total" />
                  </th>
                  <th className="text-center py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-24">Status</th>
                  <th className="text-center py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider w-20">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-2 px-3">
                      <span className="font-mono text-sm font-medium text-gray-900">#{transaction.id}</span>
                    </td>
                    <td className="py-2 px-3">
                      <span className="text-sm text-gray-600">{formatDate(transaction.created_at)}</span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className="text-sm text-gray-600">
                        {transaction.items?.length || 0}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <span className="inline-flex items-center gap-1 text-sm">
                        <span>{getPaymentIcon(transaction.payment_method)}</span>
                        <span className="capitalize">{transaction.payment_method}</span>
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className="text-sm text-gray-600">${(transaction.subtotal ?? 0).toFixed(2)}</span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className="text-sm text-gray-500">${(transaction.tax ?? 0).toFixed(2)}</span>
                    </td>
                    <td className="py-2 px-3 text-right">
                      <span className="font-semibold text-gray-900">${(transaction.total ?? 0).toFixed(2)}</span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${getStatusBadge(transaction.status)}`}>
                        {transaction.status}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => openTransactionDetails(transaction)}
                        className="text-sky-600 hover:text-sky-800 text-sm font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transaction Details Modal */}
      {showModal && selectedTransaction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-sky-500 to-sky-600 text-white p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-xl font-bold">Transaction #{selectedTransaction.id}</h2>
                  <p className="text-sky-100 text-sm mt-1">{formatDate(selectedTransaction.created_at)}</p>
                </div>
                <button 
                  onClick={() => setShowModal(false)}
                  className="text-white/80 hover:text-white"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {/* Status & Payment */}
              <div className="flex gap-4 mb-6">
                <div className="flex-1 bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Status</p>
                  <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${getStatusBadge(selectedTransaction.status)}`}>
                    {selectedTransaction.status}
                  </span>
                </div>
                <div className="flex-1 bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Payment Method</p>
                  <p className="text-lg font-medium capitalize">
                    {getPaymentIcon(selectedTransaction.payment_method)} {selectedTransaction.payment_method}
                  </p>
                </div>
              </div>

              {/* Items */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">Items</h3>
                {selectedTransaction.items && selectedTransaction.items.length > 0 ? (
                  <div className="space-y-2">
                    {selectedTransaction.items.map((item) => (
                      <div key={item.id} className="flex justify-between items-center bg-gray-50 rounded-lg p-3">
                        <div>
                          <p className="font-medium text-gray-900">{item.product_name}</p>
                          <p className="text-sm text-gray-500">
                            {item.quantity} × ${(item.unit_price ?? 0).toFixed(2)}
                            {(item.discount ?? 0) > 0 && <span className="text-orange-600 ml-2">(-${(item.discount ?? 0).toFixed(2)})</span>}
                          </p>
                        </div>
                        <p className="font-semibold">${(item.total ?? 0).toFixed(2)}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No item details available</p>
                )}
              </div>

              {/* Totals */}
              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Subtotal</span>
                  <span>${(selectedTransaction.subtotal ?? 0).toFixed(2)}</span>
                </div>
                {(selectedTransaction.discount ?? 0) > 0 && (
                  <div className="flex justify-between text-sm text-orange-600">
                    <span>Discount</span>
                    <span>-${(selectedTransaction.discount ?? 0).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Tax</span>
                  <span>${(selectedTransaction.tax ?? 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold border-t pt-2 mt-2">
                  <span>Total</span>
                  <span className="text-green-600">${(selectedTransaction.total ?? 0).toFixed(2)}</span>
                </div>
              </div>

              {/* Notes */}
              {selectedTransaction.notes && (
                <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
                  <p className="text-xs text-yellow-800 uppercase tracking-wider mb-1">Notes</p>
                  <p className="text-sm text-yellow-900">{selectedTransaction.notes}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end gap-3">
              <button
                onClick={() => window.print()}
                className="btn btn-outline"
              >
                🖨️ Print
              </button>
              <button
                onClick={() => setShowModal(false)}
                className="btn btn-primary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TransactionsPage() {
  return (
    <ProtectedRoute>
      <TransactionsContent />
    </ProtectedRoute>
  );
}
