'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Store {
  id: number;
  name: string;
  code: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  state?: string;
  country: string;
  is_active: boolean;
  total_sales?: number;
  transaction_count?: number;
  inventory_value?: number;
  staff_count?: number;
}

interface Transfer {
  id: number;
  transfer_number: string;
  from_store_id: number;
  to_store_id: number;
  status: string;
  priority: string;
  total_items: number;
  total_quantity: number;
  total_value: number;
  requested_at: string;
}

export default function StoresPage() {
  const router = useRouter();
  const [stores, setStores] = useState<Store[]>([]);
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stores' | 'transfers' | 'analytics'>('stores');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [storesRes, transfersRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/stores', { headers }),
        fetch('http://localhost:8000/api/v1/stores/transfers', { headers }),
      ]);

      if (storesRes.ok) {
        setStores(await storesRes.json());
      }
      if (transfersRes.ok) {
        setTransfers(await transfersRes.json());
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStoreName = (storeId: number) => {
    const store = stores.find((s: Store) => s.id === storeId);
    return store?.name || `Store #${storeId}`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-blue-100 text-blue-800';
      case 'in_transit': return 'bg-purple-100 text-purple-800';
      case 'received': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Multi-Store Management</h1>
              <p className="text-sm text-gray-500">Manage locations, transfers, and analytics</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowTransferModal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                New Transfer
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add Store
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {(['stores', 'transfers', 'analytics'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                    activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stores Tab */}
        {activeTab === 'stores' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stores.map((store: Store) => (
              <div
                key={store.id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/admin/stores/${store.id}`)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{store.name}</h3>
                    <p className="text-sm text-gray-500">{store.code}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    store.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {store.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                {store.city && (
                  <p className="text-sm text-gray-600 mb-4">
                    📍 {store.city}, {store.state}
                  </p>
                )}

                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <p className="text-xs text-gray-500">Today&apos;s Sales</p>
                    <p className="text-lg font-semibold text-green-600">
                      ${(store.total_sales || 0).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Transactions</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {store.transaction_count || 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Inventory Value</p>
                    <p className="text-lg font-semibold text-blue-600">
                      ${(store.inventory_value || 0).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Staff</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {store.staff_count || 0}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {stores.length === 0 && (
              <div className="col-span-full text-center py-12">
                <div className="text-6xl mb-4">🏪</div>
                <h3 className="text-lg font-medium text-gray-900">No stores yet</h3>
                <p className="text-gray-500 mb-4">Add your first store to get started</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Store
                </button>
              </div>
            )}
          </div>
        )}

        {/* Transfers Tab */}
        {activeTab === 'transfers' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Transfer #</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">From → To</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transfers.map((transfer: Transfer) => (
                  <tr key={transfer.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {transfer.transfer_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getStoreName(transfer.from_store_id)} → {getStoreName(transfer.to_store_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {transfer.total_items} items ({transfer.total_quantity} units)
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${transfer.total_value.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(transfer.status)}`}>
                        {transfer.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(transfer.requested_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => router.push(`/admin/stores/transfers/${transfer.id}`)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {transfers.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📦</div>
                <h3 className="text-lg font-medium text-gray-900">No transfers yet</h3>
                <p className="text-gray-500">Create your first inter-store transfer</p>
              </div>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-500">Total Stores</p>
                <p className="text-3xl font-bold text-gray-900">{stores.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-500">Total Sales (Today)</p>
                <p className="text-3xl font-bold text-green-600">
                  ${stores.reduce((sum: number, s: Store) => sum + (s.total_sales || 0), 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-500">Pending Transfers</p>
                <p className="text-3xl font-bold text-yellow-600">
                  {transfers.filter((t: Transfer) => t.status === 'pending').length}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-sm text-gray-500">Total Inventory Value</p>
                <p className="text-3xl font-bold text-blue-600">
                  ${stores.reduce((sum: number, s: Store) => sum + (s.inventory_value || 0), 0).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Store Comparison */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Store Performance Comparison</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-4">Store</th>
                      <th className="text-right py-2 px-4">Sales</th>
                      <th className="text-right py-2 px-4">Transactions</th>
                      <th className="text-right py-2 px-4">Avg Ticket</th>
                      <th className="text-right py-2 px-4">Inventory</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stores.map((store: Store) => (
                      <tr key={store.id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 font-medium">{store.name}</td>
                        <td className="py-3 px-4 text-right text-green-600">
                          ${(store.total_sales || 0).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {store.transaction_count || 0}
                        </td>
                        <td className="py-3 px-4 text-right">
                          ${store.transaction_count ? ((store.total_sales || 0) / store.transaction_count).toFixed(2) : '0.00'}
                        </td>
                        <td className="py-3 px-4 text-right text-blue-600">
                          ${(store.inventory_value || 0).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Store Modal */}
      {showCreateModal && (
        <CreateStoreModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            fetchData();
          }}
        />
      )}

      {/* Create Transfer Modal */}
      {showTransferModal && (
        <CreateTransferModal
          stores={stores}
          onClose={() => setShowTransferModal(false)}
          onCreated={() => {
            setShowTransferModal(false);
            fetchData();
          }}
        />
      )}
    </div>
  );
}

function CreateStoreModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    email: '',
    phone: '',
    address_line1: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/stores', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        onCreated();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create store');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Add New Store</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Store Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Store Code *</label>
              <input
                type="text"
                required
                placeholder="STORE01"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Address</label>
            <input
              type="text"
              value={formData.address_line1}
              onChange={(e) => setFormData({ ...formData, address_line1: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">City</label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">State</label>
              <input
                type="text"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">ZIP</label>
              <input
                type="text"
                value={formData.postal_code}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Store'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CreateTransferModal({
  stores,
  onClose,
  onCreated,
}: {
  stores: Store[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [formData, setFormData] = useState({
    from_store_id: '',
    to_store_id: '',
    priority: 'normal',
    reason: '',
    items: [] as { product_id: number; quantity: number; name?: string }[],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.items.length === 0) {
      setError('Add at least one item to transfer');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/v1/stores/transfers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          from_store_id: parseInt(formData.from_store_id),
          to_store_id: parseInt(formData.to_store_id),
          priority: formData.priority,
          reason: formData.reason,
          items: formData.items.map((i: { product_id: number; quantity: number }) => ({ product_id: i.product_id, quantity: i.quantity })),
        }),
      });

      if (response.ok) {
        onCreated();
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to create transfer');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Create Transfer</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">From Store *</label>
              <select
                required
                value={formData.from_store_id}
                onChange={(e) => setFormData({ ...formData, from_store_id: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">Select store</option>
                {stores.filter(s => s.id.toString() !== formData.to_store_id).map((store) => (
                  <option key={store.id} value={store.id}>{store.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">To Store *</label>
              <select
                required
                value={formData.to_store_id}
                onChange={(e) => setFormData({ ...formData, to_store_id: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">Select store</option>
                {stores.filter(s => s.id.toString() !== formData.from_store_id).map((store) => (
                  <option key={store.id} value={store.id}>{store.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Priority</label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Reason</label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              rows={2}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Why is this transfer needed?"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">Items *</label>
              <button
                type="button"
                onClick={() => {
                  const productId = prompt('Enter product ID:');
                  const quantity = prompt('Enter quantity:');
                  if (productId && quantity) {
                    setFormData({
                      ...formData,
                      items: [...formData.items, { product_id: parseInt(productId), quantity: parseInt(quantity) }],
                    });
                  }
                }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + Add Item
              </button>
            </div>
            
            {formData.items.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No items added yet</p>
            ) : (
              <div className="space-y-2">
                {formData.items.map((item: { product_id: number; quantity: number }, index: number) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm">Product #{item.product_id} × {item.quantity}</span>
                    <button
                      type="button"
                      onClick={() => {
                        setFormData({
                          ...formData,
                          items: formData.items.filter((_: { product_id: number; quantity: number }, i: number) => i !== index),
                        });
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Transfer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
