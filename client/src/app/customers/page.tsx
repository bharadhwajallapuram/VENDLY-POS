'use client';

// ===========================================
// Vendly POS - Customers Page (Full Management)
// ===========================================

import { useState, useEffect, useCallback } from 'react';
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

// Filter and sort types
type SortField = 'name' | 'loyalty_points' | 'created_at' | 'email';
type FilterStatus = 'all' | 'active' | 'inactive';

function CustomersContent() {
  const [customers, setCustomers] = useState<CustomerOut[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<CustomerOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  
  // Filter and sort state
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerOut | null>(null);
  const [editingCustomer, setEditingCustomer] = useState<CustomerOut | null>(null);
  const [formData, setFormData] = useState<CustomerFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  
  // Loyalty adjustment modal
  const [showLoyaltyModal, setShowLoyaltyModal] = useState(false);
  const [loyaltyCustomer, setLoyaltyCustomer] = useState<CustomerOut | null>(null);
  const [loyaltyPoints, setLoyaltyPoints] = useState(0);
  const [loyaltyReason, setLoyaltyReason] = useState('');

  const fetchCustomers = useCallback(async () => {
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
  }, [search]);

  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  // Apply filtering and sorting
  useEffect(() => {
    let result = customers;

    // Apply status filter
    if (filterStatus !== 'all') {
      result = result.filter(c =>
        filterStatus === 'active' ? c.is_active : !c.is_active
      );
    }

    // Sort
    result.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (b[sortField] as string).toLowerCase();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    setFilteredCustomers(result);
  }, [customers, filterStatus, sortField, sortOrder]);

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

  const openDetailModal = (customer: CustomerOut) => {
    setSelectedCustomer(customer);
    setShowDetailModal(true);
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
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold">Customers</h1>
          <p className="text-xs md:text-sm text-gray-600">Manage customer profiles and loyalty program</p>
        </div>
        <button onClick={openAddModal} className="btn btn-success w-full sm:w-auto">
          + Add Customer
        </button>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3 md:space-y-4">
        {/* Search Bar */}
        <div className="card">
          <input
            type="text"
            placeholder="Search by name, email, or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input w-full"
          />
        </div>

        {/* Filters and Sort */}
        <div className="card space-y-3 md:space-y-0 md:flex md:flex-wrap md:gap-4">
          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <label className="text-xs md:text-sm font-medium whitespace-nowrap">Status:</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
              className="input px-2 md:px-3 py-2 flex-1 md:flex-none"
            >
              <option value="all">All Customers</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <div className="flex flex-col md:flex-row md:items-center gap-2">
            <label className="text-xs md:text-sm font-medium whitespace-nowrap">Sort by:</label>
            <div className="flex gap-2">
              <select
                value={sortField}
                onChange={(e) => setSortField(e.target.value as SortField)}
                className="input px-2 md:px-3 py-2 flex-1"
              >
                <option value="name">Name</option>
                <option value="loyalty_points">Loyalty Points</option>
                <option value="created_at">Date Added</option>
                <option value="email">Email</option>
              </select>
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="btn px-2 md:px-3 py-2"
                title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            </div>
          </div>

          <div className="text-xs md:text-sm text-gray-600 md:ml-auto pt-2 md:pt-0">
            {filteredCustomers.length} of {customers.length} customers
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-100 text-red-700 p-3 md:p-4 rounded-lg flex justify-between items-center gap-3">
          <span className="text-sm md:text-base">{error}</span>
          <button onClick={() => setError(null)} className="text-red-700 font-bold flex-shrink-0">
            ✕
          </button>
        </div>
      )}

      {/* Customer List */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <p className="text-center py-8 text-gray-500 text-sm md:text-base">Loading customers...</p>
        ) : filteredCustomers.length === 0 ? (
          <p className="text-center py-8 text-gray-500 text-sm md:text-base">
            {customers.length === 0
              ? 'No customers yet. Add your first customer!'
              : 'No customers match your filters.'}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs md:text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-2 md:px-4 font-medium text-gray-700">Name</th>
                  <th className="text-left py-3 px-2 md:px-4 font-medium text-gray-700 hidden sm:table-cell">Email</th>
                  <th className="text-left py-3 px-2 md:px-4 font-medium text-gray-700 hidden md:table-cell">Phone</th>
                  <th className="text-right py-3 px-2 md:px-4 font-medium text-gray-700">Points</th>
                  <th className="text-center py-3 px-2 md:px-4 font-medium text-gray-700 hidden sm:table-cell">Status</th>
                  <th className="text-center py-3 px-2 md:px-4 font-medium text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer) => (
                  <tr key={customer.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-2 md:px-4 font-medium text-xs md:text-sm">
                      <div>{customer.name}</div>
                      <div className="text-gray-500 text-xs md:hidden">{customer.email || '-'}</div>
                    </td>
                    <td className="py-3 px-2 md:px-4 text-gray-600 hidden sm:table-cell text-xs md:text-sm">
                      {customer.email || '-'}
                    </td>
                    <td className="py-3 px-2 md:px-4 text-gray-600 hidden md:table-cell text-xs md:text-sm">
                      {customer.phone || '-'}
                    </td>
                    <td className="py-3 px-2 md:px-4 text-right">
                      <button
                        onClick={() => openLoyaltyModal(customer)}
                        className="text-gray-700 hover:underline font-medium text-xs md:text-sm"
                      >
                        {customer.loyalty_points}
                      </button>
                    </td>
                    <td className="py-3 px-2 md:px-4 text-center hidden sm:table-cell">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          customer.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {customer.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3 px-2 md:px-4">
                      <div className="flex gap-1 justify-center flex-wrap">
                        <button
                          onClick={() => openDetailModal(customer)}
                          className="text-gray-700 hover:underline text-xs px-2 py-1 rounded hover:bg-gray-50"
                        >
                          View
                        </button>
                        <button
                          onClick={() => openEditModal(customer)}
                          className="text-gray-700 hover:underline text-xs px-2 py-1 rounded hover:bg-gray-50"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(customer.id)}
                          className="text-red-600 hover:underline text-xs px-2 py-1 rounded hover:bg-red-50"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Detail Modal */}
      {showDetailModal && selectedCustomer && (
        <div className="modal" onClick={() => setShowDetailModal(false)}>
          <div
            className="modal-content lg"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4 md:mb-6 pb-3 md:pb-4 border-b">
              <h2 className="text-lg md:text-xl font-bold pr-4">{selectedCustomer.name}</h2>
              <button
                onClick={() => setShowDetailModal(false)}
                className="flex-shrink-0 text-gray-500 hover:text-gray-700 text-2xl md:text-xl leading-none"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Contact Information */}
              <div>
                <h3 className="text-sm font-bold text-gray-700 mb-4">Contact Information</h3>
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-gray-500 text-xs">Email</p>
                    <p className="font-medium break-all">{selectedCustomer.email || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Phone</p>
                    <p className="font-medium">{selectedCustomer.phone || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Address</p>
                    <p className="font-medium">{selectedCustomer.address || 'Not provided'}</p>
                  </div>
                </div>
              </div>

              {/* Loyalty Information */}
              <div>
                <h3 className="text-sm font-bold text-gray-700 mb-4">Loyalty Program</h3>
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-gray-500 text-xs">Current Points</p>
                    <p className="text-3xl font-bold text-gray-900">{selectedCustomer.loyalty_points}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Status</p>
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        selectedCustomer.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {selectedCustomer.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Member Since</p>
                    <p className="font-medium">
                      {new Date(selectedCustomer.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Notes */}
            {selectedCustomer.notes && (
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-sm font-bold text-gray-700 mb-3">Notes</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{selectedCustomer.notes}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row justify-end gap-2 md:gap-3 pt-6 mt-6 border-t">
              <button
                onClick={() => {
                  setShowDetailModal(false);
                  openLoyaltyModal(selectedCustomer);
                }}
                className="btn btn-info w-full sm:w-auto"
              >
                Adjust Loyalty
              </button>
              <button
                onClick={() => {
                  setShowDetailModal(false);
                  openEditModal(selectedCustomer);
                }}
                className="btn btn-primary w-full sm:w-auto"
              >
                Edit Customer
              </button>
              <button
                onClick={() => setShowDetailModal(false)}
                className="btn w-full sm:w-auto"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Customer Form Modal */}
      {showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4 md:mb-6 pb-3 md:pb-4 border-b">
              <h2 className="text-lg md:text-xl font-bold pr-4">
                {editingCustomer ? 'Edit Customer' : 'Add New Customer'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="flex-shrink-0 text-gray-500 hover:text-gray-700 text-2xl md:text-xl leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3 md:space-y-4">
              {/* Name */}
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="Customer full name"
                  required
                  autoFocus
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input w-full"
                  placeholder="customer@example.com"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input w-full"
                  placeholder="(555) 123-4567"
                />
              </div>

              {/* Address */}
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">Address</label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="input w-full"
                  rows={2}
                  placeholder="Street address, city, state, zip"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="input w-full"
                  rows={3}
                  placeholder="Add any notes or special instructions"
                />
              </div>

              {/* Loyalty Points (only for new customers) */}
              {!editingCustomer && (
                <div>
                  <label className="block text-xs md:text-sm font-medium mb-1">
                    Initial Loyalty Points
                  </label>
                  <input
                    type="number"
                    value={formData.loyalty_points}
                    onChange={(e) =>
                      setFormData({ ...formData, loyalty_points: Math.max(0, parseInt(e.target.value) || 0) })
                    }
                    className="input w-full"
                    min="0"
                    placeholder="0"
                  />
                </div>
              )}

              {/* Active Status */}
              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4 cursor-pointer"
                />
                <label htmlFor="is_active" className="text-xs md:text-sm font-medium cursor-pointer">
                  Mark as Active Customer
                </label>
              </div>

              {/* Actions */}
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 md:gap-3 pt-4 md:pt-6 border-t mt-4 md:mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn w-full sm:w-auto"
                  disabled={saving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary w-full sm:w-auto" disabled={saving}>
                  {saving ? 'Saving...' : editingCustomer ? 'Update Customer' : 'Create Customer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loyalty Adjustment Modal */}
      {showLoyaltyModal && loyaltyCustomer && (
        <div className="modal" onClick={() => setShowLoyaltyModal(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4 md:mb-6 pb-3 md:pb-4 border-b">
              <h2 className="text-lg md:text-xl font-bold pr-4">Adjust Loyalty Points</h2>
              <button
                onClick={() => setShowLoyaltyModal(false)}
                className="flex-shrink-0 text-gray-500 hover:text-gray-700 text-2xl md:text-xl leading-none"
              >
                ✕
              </button>
            </div>

            <div className="bg-gray-50 p-4 md:p-5 rounded-lg mb-6">
              <p className="text-xs md:text-sm text-gray-600">Customer</p>
              <p className="text-lg md:text-xl font-bold">{loyaltyCustomer.name}</p>
              <p className="text-xs md:text-sm text-gray-600 mt-3">Current Points</p>
              <p className="text-3xl md:text-4xl font-bold text-gray-900">{loyaltyCustomer.loyalty_points}</p>
            </div>

            <form onSubmit={handleLoyaltyAdjust} className="space-y-3 md:space-y-4">
              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">
                  Points to Add/Remove
                </label>
                <input
                  type="number"
                  value={loyaltyPoints}
                  onChange={(e) => setLoyaltyPoints(parseInt(e.target.value) || 0)}
                  className="input w-full text-lg md:text-base font-bold"
                  placeholder="e.g., 50 or -25"
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-2">
                  • Enter positive numbers to add points
                  <br />
                  • Enter negative numbers to remove points
                </p>
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium mb-1">Reason (optional)</label>
                <input
                  type="text"
                  value={loyaltyReason}
                  onChange={(e) => setLoyaltyReason(e.target.value)}
                  className="input w-full"
                  placeholder="e.g., Birthday bonus, Complaint resolution"
                />
              </div>

              {/* Preview */}
              <div className="bg-gray-50 p-3 md:p-4 rounded-lg">
                <p className="text-xs text-gray-600">New Balance After Adjustment:</p>
                <p
                  className={`text-2xl md:text-3xl font-bold ${
                    loyaltyPoints > 0 ? 'text-green-600' : loyaltyPoints < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}
                >
                  {loyaltyCustomer.loyalty_points + loyaltyPoints}
                </p>
              </div>

              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 md:gap-3 pt-4 md:pt-6 border-t mt-4 md:mt-6">
                <button
                  type="button"
                  onClick={() => setShowLoyaltyModal(false)}
                  className="btn w-full sm:w-auto"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary w-full sm:w-auto"
                  disabled={loyaltyPoints === 0}
                >
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
