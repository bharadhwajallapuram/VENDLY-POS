'use client';

// ===========================================
// Vendly POS - Discounts & Promotions Settings
// ===========================================

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { couponsApi, CouponOut } from '@/lib/api';

interface Coupon {
  id: number;
  code: string;
  type: 'percent' | 'amount';
  value: number;
  maxOff?: number;
  minOrder?: number;
  active: boolean;
  expiresAt?: string;
  usageCount: number;
  stackable: boolean;
}

// Transform API response to local format
function transformCoupon(apiCoupon: CouponOut): Coupon {
  return {
    id: apiCoupon.id,
    code: apiCoupon.code,
    type: apiCoupon.type,
    value: apiCoupon.value,
    maxOff: apiCoupon.max_off ?? undefined,
    minOrder: apiCoupon.min_order ?? undefined,
    active: apiCoupon.active,
    expiresAt: apiCoupon.expires_at ?? undefined,
    usageCount: apiCoupon.usage_count,
    stackable: apiCoupon.stackable,
  };
}

function DiscountsContent() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState<Coupon | null>(null);
  
  // Form state
  const [formCode, setFormCode] = useState('');
  const [formType, setFormType] = useState<'percent' | 'amount'>('percent');
  const [formValue, setFormValue] = useState(0);
  const [formMaxOff, setFormMaxOff] = useState<number | ''>('');
  const [formMinOrder, setFormMinOrder] = useState<number | ''>('');
  const [formExpiresAt, setFormExpiresAt] = useState('');
  const [formActive, setFormActive] = useState(true);
  const [formStackable, setFormStackable] = useState(true);

  // Fetch coupons from API
  useEffect(() => {
    fetchCoupons();
  }, []);

  async function fetchCoupons() {
    try {
      setLoading(true);
      setError(null);
      const data = await couponsApi.list();
      setCoupons(data.map(transformCoupon));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load coupons');
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setFormCode('');
    setFormType('percent');
    setFormValue(0);
    setFormMaxOff('');
    setFormMinOrder('');
    setFormExpiresAt('');
    setFormActive(true);
    setFormStackable(true);
    setEditingCoupon(null);
  }

  function openAddModal() {
    resetForm();
    setShowAddModal(true);
  }

  function openEditModal(coupon: Coupon) {
    setFormCode(coupon.code);
    setFormType(coupon.type);
    setFormValue(coupon.value);
    setFormMaxOff(coupon.maxOff || '');
    setFormMinOrder(coupon.minOrder || '');
    setFormExpiresAt(coupon.expiresAt || '');
    setFormActive(coupon.active);
    setFormStackable(coupon.stackable);
    setEditingCoupon(coupon);
    setShowAddModal(true);
  }

  async function saveCoupon() {
    if (!formCode.trim()) {
      alert('Coupon code is required');
      return;
    }
    if (formValue <= 0) {
      alert('Discount value must be greater than 0');
      return;
    }

    try {
      setSaving(true);
      
      if (editingCoupon) {
        // Update existing coupon
        const updated = await couponsApi.update(editingCoupon.id, {
          code: formCode.toUpperCase().trim(),
          type: formType,
          value: formValue,
          max_off: formMaxOff ? Number(formMaxOff) : null,
          min_order: formMinOrder ? Number(formMinOrder) : null,
          expires_at: formExpiresAt || null,
          active: formActive,
          stackable: formStackable,
        });
        setCoupons(coupons.map(c => c.id === editingCoupon.id ? transformCoupon(updated) : c));
      } else {
        // Create new coupon
        const created = await couponsApi.create({
          code: formCode.toUpperCase().trim(),
          type: formType,
          value: formValue,
          max_off: formMaxOff ? Number(formMaxOff) : null,
          min_order: formMinOrder ? Number(formMinOrder) : null,
          expires_at: formExpiresAt || null,
          active: formActive,
          stackable: formStackable,
        });
        setCoupons([transformCoupon(created), ...coupons]);
      }

      setShowAddModal(false);
      resetForm();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to save coupon');
    } finally {
      setSaving(false);
    }
  }

  async function deleteCoupon(coupon: Coupon) {
    if (confirm(`Delete coupon ${coupon.code}?`)) {
      try {
        await couponsApi.del(coupon.id);
        setCoupons(coupons.filter(c => c.id !== coupon.id));
      } catch (err) {
        alert(err instanceof Error ? err.message : 'Failed to delete coupon');
      }
    }
  }

  async function toggleCoupon(coupon: Coupon) {
    try {
      const updated = await couponsApi.toggle(coupon.id);
      setCoupons(coupons.map(c => c.id === coupon.id ? transformCoupon(updated) : c));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to toggle coupon');
    }
  }

  const activeCoupons = coupons.filter(c => c.active).length;
  const totalUsage = coupons.reduce((sum, c) => sum + c.usageCount, 0);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 -mt-6 -mx-4 px-4 py-8">
        <div className="max-w-6xl mx-auto flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
            <p className="text-slate-500">Loading coupons...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 -mt-6 -mx-4 px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
            <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-semibold text-red-700 mb-2">Failed to load coupons</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchCoupons}
              className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-semibold px-5 py-2.5 rounded-xl transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 -mt-6 -mx-4 px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800">Discounts & Promotions</h1>
          <p className="text-slate-500 mt-1">Create and manage coupon codes for your store</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-800">{coupons.length}</p>
                <p className="text-sm text-slate-500">Total Coupons</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-800">{activeCoupons}</p>
                <p className="text-sm text-slate-500">Active Coupons</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-800">{totalUsage}</p>
                <p className="text-sm text-slate-500">Total Redemptions</p>
              </div>
            </div>
          </div>
        </div>

        {/* Add Coupon Button */}
        <div className="flex justify-end mb-6">
          <button 
            onClick={openAddModal}
            className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-3 rounded-xl transition-colors shadow-lg shadow-emerald-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Coupon
          </button>
        </div>

        {/* Coupons Grid */}
        {coupons.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center shadow-sm border border-slate-200">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-slate-700 mb-2">No coupons yet</h3>
            <p className="text-slate-500 mb-6">Create your first coupon to start offering discounts</p>
            <button 
              onClick={openAddModal}
              className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-5 py-3 rounded-xl transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create First Coupon
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {coupons.map((coupon) => (
              <div 
                key={coupon.code} 
                className={`bg-white rounded-2xl shadow-sm border overflow-hidden transition-all hover:shadow-md ${
                  coupon.active ? 'border-slate-200' : 'border-slate-200 opacity-60'
                }`}
              >
                {/* Coupon Header */}
                <div className={`px-5 py-4 ${coupon.active ? 'bg-gradient-to-r from-emerald-500 to-teal-500' : 'bg-slate-400'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xl font-bold text-white tracking-wider">{coupon.code}</span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      coupon.active ? 'bg-white/20 text-white' : 'bg-white/30 text-white'
                    }`}>
                      {coupon.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
                
                {/* Coupon Body */}
                <div className="p-5">
                  {/* Discount Value */}
                  <div className="text-center mb-4 pb-4 border-b border-dashed border-slate-200">
                    <span className="text-4xl font-bold text-slate-800">
                      {coupon.type === 'percent' ? `${coupon.value}%` : `$${coupon.value}`}
                    </span>
                    <p className="text-sm text-slate-500 mt-1">
                      {coupon.type === 'percent' ? 'Percentage Off' : 'Fixed Discount'}
                    </p>
                  </div>
                  
                  {/* Coupon Details */}
                  <div className="space-y-2 text-sm mb-4">
                    {coupon.maxOff && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        Max discount: ${coupon.maxOff}
                      </div>
                    )}
                    {coupon.minOrder && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        Min order: ${coupon.minOrder}
                      </div>
                    )}
                    {coupon.expiresAt && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Expires: {new Date(coupon.expiresAt).toLocaleDateString()}
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-slate-600">
                      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {coupon.usageCount} redemptions
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      {coupon.stackable ? 'Stackable' : 'Non-stackable'}
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleCoupon(coupon)}
                      className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                        coupon.active 
                          ? 'bg-amber-50 text-amber-700 hover:bg-amber-100' 
                          : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                      }`}
                    >
                      {coupon.active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => openEditModal(coupon)}
                      className="py-2 px-3 rounded-lg text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => deleteCoupon(coupon)}
                      className="py-2 px-3 rounded-lg text-sm font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Settings Card */}
        <div className="mt-8 bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Checkout Discount Settings
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Manual Discount Permission
              </label>
              <select className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors">
                <option value="all">All Staff</option>
                <option value="managers">Managers Only</option>
                <option value="none">Disabled</option>
              </select>
              <p className="text-xs text-slate-500 mt-1">Who can apply manual discounts at checkout</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Maximum Manual Discount
              </label>
              <div className="relative">
                <input 
                  type="number" 
                  className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors" 
                  defaultValue={20}
                  min={0}
                  max={100}
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">%</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Max discount staff can apply without approval</p>
            </div>
          </div>
        </div>
      </div>

      {/* Add/Edit Coupon Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-4">
              <h2 className="text-xl font-semibold text-white">
                {editingCoupon ? 'Edit Coupon' : 'Create New Coupon'}
              </h2>
              <p className="text-emerald-100 text-sm">
                {editingCoupon ? 'Update the coupon details below' : 'Fill in the details to create a new coupon'}
              </p>
            </div>
            
            {/* Modal Body */}
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Coupon Code <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-slate-700 uppercase placeholder:normal-case focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors disabled:bg-slate-100"
                  placeholder="e.g., SUMMER20"
                  value={formCode}
                  onChange={(e) => setFormCode(e.target.value)}
                  disabled={!!editingCoupon}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Discount Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                    value={formType}
                    onChange={(e) => setFormType(e.target.value as 'percent' | 'amount')}
                  >
                    <option value="percent">Percentage (%)</option>
                    <option value="amount">Fixed Amount ($)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Value <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                      placeholder={formType === 'percent' ? '10' : '5.00'}
                      min={0}
                      step={formType === 'percent' ? 1 : 0.01}
                      value={formValue || ''}
                      onChange={(e) => setFormValue(parseFloat(e.target.value) || 0)}
                    />
                    <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400">
                      {formType === 'percent' ? '%' : '$'}
                    </span>
                  </div>
                </div>
              </div>

              {formType === 'percent' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Maximum Discount Cap
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                    <input
                      type="number"
                      className="w-full px-4 py-2.5 pl-8 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                      placeholder="No limit"
                      min={0}
                      step={0.01}
                      value={formMaxOff}
                      onChange={(e) => setFormMaxOff(e.target.value ? parseFloat(e.target.value) : '')}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Optional: Limit the maximum discount amount</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Minimum Order
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                    <input
                      type="number"
                      className="w-full px-4 py-2.5 pl-8 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                      placeholder="0.00"
                      min={0}
                      step={0.01}
                      value={formMinOrder}
                      onChange={(e) => setFormMinOrder(e.target.value ? parseFloat(e.target.value) : '')}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Expiration Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-xl text-slate-700 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                    value={formExpiresAt}
                    onChange={(e) => setFormExpiresAt(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-xl">
                <input
                  type="checkbox"
                  id="formActive"
                  checked={formActive}
                  onChange={(e) => setFormActive(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <label htmlFor="formActive" className="text-sm font-medium text-slate-700">
                  Active immediately
                  <span className="block text-xs text-slate-500 font-normal">Coupon can be used right away</span>
                </label>
              </div>

              <div className="flex items-center gap-3 p-3 bg-amber-50 rounded-xl">
                <input
                  type="checkbox"
                  id="formStackable"
                  checked={formStackable}
                  onChange={(e) => setFormStackable(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                />
                <label htmlFor="formStackable" className="text-sm font-medium text-slate-700">
                  Stackable with other coupons
                  <span className="block text-xs text-slate-500 font-normal">If unchecked, this coupon cannot be combined with others</span>
                </label>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-slate-50 flex gap-3 justify-end">
              <button
                onClick={() => { setShowAddModal(false); resetForm(); }}
                className="px-5 py-2.5 rounded-xl text-slate-700 font-medium hover:bg-slate-200 transition-colors"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={saveCoupon}
                disabled={saving}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-medium hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : editingCoupon ? 'Save Changes' : 'Create Coupon'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DiscountsPage() {
  return (
    <ProtectedRoute>
      <DiscountsContent />
    </ProtectedRoute>
  );
}
