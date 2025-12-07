'use client';

// ===========================================
// Vendly POS - Customers Page
// ===========================================

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Customers, CustomerOut, CustomerIn } from '@/lib/api';

interface CustomerFormData {
  name: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
  loyalty_points: number;
  is_active: boolean;
}

const emptyForm: CustomerFormData = {
  name: '',
  email: '',
  phone: '',
  address: '',
  notes: '',
  loyalty_points: 0,
  is_active: true,
};

function CustomersContent() {
  const [customers, setCustomers] = useState<CustomerOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<CustomerOut | null>(null);
  const [formData, setFormData] = useState<CustomerFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  
  // Loyalty adjustment modal
  const [showLoyaltyModal, setShowLoyaltyModal] = useState(false);
  const [loyaltyCustomer, setLoyaltyCustomer] = useState<CustomerOut | null>(null);
  const [loyaltyPoints, setLoyaltyPoints] = useState(0);
  const [loyaltyReason, setLoyaltyReason] = useState('');

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const data = await Customers.list(search || undefined);
      setCustomers(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  const openAddModal = () => {
    setEditingCustomer(null);
    setFormData(emptyForm);
    setShowModal(true);
  };

  const openEditModal = (customer: CustomerOut) => {
    setEditingCustomer(customer);
    setFormData({
      name: customer.name,
      email: customer.email || '',
      phone: customer.phone || '',
      address: customer.address || '',
      notes: customer.notes || '',
      loyalty_points: customer.loyalty_points,
      is_active: customer.is_active,
    });
    setShowModal(true);
  };

  const openLoyaltyModal = (customer: CustomerOut) => {
    setLoyaltyCustomer(customer);
    setLoyaltyPoints(0);
    setLoyaltyReason('');
    setShowLoyaltyModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const customerData: CustomerIn = {
        name: formData.name,
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        address: formData.address || undefined,
        notes: formData.notes || undefined,
        loyalty_points: formData.loyalty_points,
        is_active: formData.is_active,
      };

      if (editingCustomer) {
        await Customers.update(editingCustomer.id, customerData);
      } else {
        await Customers.create(customerData);
      }

      setShowModal(false);
      fetchCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save customer');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this customer?')) return;

    try {
      await Customers.del(id);
      fetchCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete customer');
    }
  };

  const handleLoyaltyAdjust = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loyaltyCustomer) return;

    try {
      await Customers.adjustLoyalty(loyaltyCustomer.id, loyaltyPoints, loyaltyReason || undefined);
      setShowLoyaltyModal(false);
      fetchCustomers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to adjust loyalty points');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Customers</h1>
        <button onClick={openAddModal} className="btn btn-success">
          + Add Customer
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <input
          type="text"
          placeholder="Search customers by name, email, or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input w-full"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-100 text-red-700 p-4 rounded-lg">
          {error}
          <button onClick={() => setError(null)} className="ml-4 underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Customer List */}
      <div className="card">
        {loading ? (
          <p className="text-center py-8 text-gray-500">Loading customers...</p>
        ) : customers.length === 0 ? (
          <p className="text-center py-8 text-gray-500">
            No customers found. Add your first customer!
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-2">Name</th>
                  <th className="text-left py-3 px-2">Email</th>
                  <th className="text-left py-3 px-2">Phone</th>
                  <th className="text-right py-3 px-2">Loyalty Points</th>
                  <th className="text-center py-3 px-2">Status</th>
                  <th className="text-right py-3 px-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr key={customer.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2 font-medium">{customer.name}</td>
                    <td className="py-3 px-2 text-gray-600">{customer.email || '-'}</td>
                    <td className="py-3 px-2 text-gray-600">{customer.phone || '-'}</td>
                    <td className="py-3 px-2 text-right">
                      <button
                        onClick={() => openLoyaltyModal(customer)}
                        className="text-blue-600 hover:underline"
                      >
                        {customer.loyalty_points} pts
                      </button>
                    </td>
                    <td className="py-3 px-2 text-center">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          customer.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {customer.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-right">
                      <button
                        onClick={() => openEditModal(customer)}
                        className="text-blue-600 hover:underline mr-3"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(customer.id)}
                        className="text-red-600 hover:underline"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Form Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {editingCustomer ? 'Edit Customer' : 'Add New Customer'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  required
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input w-full"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input w-full"
                />
              </div>

              {/* Address */}
              <div>
                <label className="block text-sm font-medium mb-1">Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input w-full"
                  rows={2}
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="input w-full"
                  rows={3}
                />
              </div>

              {/* Loyalty Points (only for new customers) */}
              {!editingCustomer && (
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Initial Loyalty Points
                  </label>
                  <input
                    type="number"
                    value={formData.loyalty_points}
                    onChange={(e) =>
                      setFormData({ ...formData, loyalty_points: parseInt(e.target.value) || 0 })
                    }
                    className="input w-full"
                    min="0"
                  />
                </div>
              )}

              {/* Active Status */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4"
                />
                <label htmlFor="is_active" className="text-sm font-medium">
                  Active Customer
                </label>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : editingCustomer ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loyalty Adjustment Modal */}
      {showLoyaltyModal && loyaltyCustomer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Adjust Loyalty Points</h2>
            <p className="text-gray-600 mb-4">
              Customer: <strong>{loyaltyCustomer.name}</strong>
              <br />
              Current Points: <strong>{loyaltyCustomer.loyalty_points}</strong>
            </p>
            <form onSubmit={handleLoyaltyAdjust} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Points to Add/Remove
                </label>
                <input
                  type="number"
                  value={loyaltyPoints}
                  onChange={(e) => setLoyaltyPoints(parseInt(e.target.value) || 0)}
                  className="input w-full"
                  placeholder="e.g., 50 or -25"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Use negative numbers to remove points
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Reason (optional)</label>
                <input
                  type="text"
                  value={loyaltyReason}
                  onChange={(e) => setLoyaltyReason(e.target.value)}
                  className="input w-full"
                  placeholder="e.g., Birthday bonus, Redemption"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowLoyaltyModal(false)}
                  className="btn"
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Adjust Points
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CustomersPage() {
  return (
    <ProtectedRoute roles={['admin']}>
      <CustomersContent />
    </ProtectedRoute>
  );
}
