'use client';

import React, { useEffect, useState } from 'react';
import { Tax, TaxRate, TaxConfiguration } from '@/lib/api';
import { toastManager } from '@/components/Toast';

interface TaxRateForm {
  region: string;
  tax_type: string;
  name: string;
  rate: number;
  state_code?: string;
  description?: string;
}

export default function TaxConfigPage() {
  const [loading, setLoading] = useState(false);
  const [region, setRegion] = useState('in');
  const [taxRates, setTaxRates] = useState<TaxRate[]>([]);
  const [config, setConfig] = useState<TaxConfiguration | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<TaxRateForm>({
    region: 'in',
    tax_type: 'gst',
    name: '',
    rate: 0,
    state_code: '',
    description: '',
  });

  const regions = [
    { code: 'in', label: 'India (GST)' },
    { code: 'au', label: 'Australia (GST)' },
    { code: 'nz', label: 'New Zealand (GST)' },
    { code: 'sg', label: 'Singapore (GST)' },
    { code: 'uk', label: 'UK (VAT)' },
    { code: 'eu', label: 'EU (VAT)' },
    { code: 'ca', label: 'Canada (GST/HST)' },
    { code: 'us', label: 'USA (Sales Tax)' },
  ];

  const taxTypes = [
    { code: 'gst', label: 'GST' },
    { code: 'vat', label: 'VAT' },
    { code: 'sales_tax', label: 'Sales Tax' },
  ];

  useEffect(() => {
    loadTaxRates();
    loadConfig();
  }, [region]);

  async function loadTaxRates() {
    setLoading(true);
    try {
      const rates = await Tax.getRates(region);
      setTaxRates(rates);
    } catch (err) {
      console.error('Failed to load tax rates:', err);
      toastManager.error('Failed to load tax rates');
    } finally {
      setLoading(false);
    }
  }

  async function loadConfig() {
    try {
      const cfg = await Tax.getConfig(region);
      setConfig(cfg);
    } catch (err) {
      console.error('Failed to load config:', err);
    }
  }

  async function handleAddRate() {
    if (!formData.name || formData.rate <= 0) {
      toastManager.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const newRate = await Tax.createRate(formData);
      setTaxRates([...taxRates, newRate]);
      setFormData({ region, tax_type: 'gst', name: '', rate: 0, state_code: '', description: '' });
      setShowForm(false);
      toastManager.success('Tax rate created successfully');
    } catch (err) {
      console.error('Failed to create tax rate:', err);
      toastManager.error('Failed to create tax rate');
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdateRate(rateId: number) {
    if (!formData.name || formData.rate <= 0) {
      toastManager.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const updated = await Tax.updateRate(rateId, {
        rate: formData.rate,
        description: formData.description,
      });
      setTaxRates(taxRates.map(r => r.id === rateId ? updated : r));
      setEditingId(null);
      setFormData({ region, tax_type: 'gst', name: '', rate: 0, state_code: '', description: '' });
      setShowForm(false);
      toastManager.success('Tax rate updated successfully');
    } catch (err) {
      console.error('Failed to update tax rate:', err);
      toastManager.error('Failed to update tax rate');
    } finally {
      setLoading(false);
    }
  }

  function startEdit(rate: TaxRate) {
    setEditingId(rate.id);
    setFormData({
      region: rate.region,
      tax_type: rate.tax_type,
      name: rate.name,
      rate: rate.rate,
      state_code: rate.state_code,
      description: rate.description,
    });
    setShowForm(true);
  }

  async function handleUpdateConfig(field: string, value: any) {
    if (!config) return;

    setLoading(true);
    try {
      const updated = await Tax.updateConfig(config.id, { [field]: value });
      setConfig(updated);
      toastManager.success('Configuration updated');
    } catch (err) {
      console.error('Failed to update config:', err);
      toastManager.error('Failed to update configuration');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Tax Configuration</h1>

      {/* Region Selector */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <label className="block text-sm font-medium mb-2">Select Region</label>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {regions.map(r => (
            <option key={r.code} value={r.code}>{r.label}</option>
          ))}
        </select>
      </div>

      {/* Configuration Settings */}
      {config && (
        <div className="mb-8 p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Configuration Settings</h2>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-2">Tax ID (GST/VAT ID)</label>
              <input
                type="text"
                value={config.tax_id || ''}
                onChange={(e) => handleUpdateConfig('tax_id', e.target.value)}
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 27AADCT5055K1Z0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Rounding Method</label>
              <select
                value={config.rounding_method}
                onChange={(e) => handleUpdateConfig('rounding_method', e.target.value)}
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="round">Round</option>
                <option value="truncate">Truncate</option>
                <option value="ceiling">Ceiling</option>
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.is_tax_exempt}
                onChange={(e) => handleUpdateConfig('is_tax_exempt', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Tax Exempt Store</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_compound_tax}
                onChange={(e) => handleUpdateConfig('enable_compound_tax', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Enable Compound Tax (CGST + SGST)</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_reverse_charge}
                onChange={(e) => handleUpdateConfig('enable_reverse_charge', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Enable Reverse Charge</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={config.enable_tax_invoice}
                onChange={(e) => handleUpdateConfig('enable_tax_invoice', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Enable Tax Invoice</span>
            </label>
          </div>
        </div>
      )}

      {/* Tax Rates */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Tax Rates for {regions.find(r => r.code === region)?.label}</h2>
          <button
            onClick={() => {
              setShowForm(!showForm);
              setEditingId(null);
              setFormData({ region, tax_type: 'gst', name: '', rate: 0, state_code: '', description: '' });
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showForm ? 'Cancel' : 'Add Rate'}
          </button>
        </div>

        {showForm && (
          <div className="mb-6 p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">{editingId ? 'Edit' : 'Add New'} Tax Rate</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Tax Type</label>
                <select
                  value={formData.tax_type}
                  onChange={(e) => setFormData({ ...formData, tax_type: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {taxTypes.map(t => (
                    <option key={t.code} value={t.code}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Rate Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., CGST, Standard VAT"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium mb-2">Rate (%)</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.rate}
                  onChange={(e) => setFormData({ ...formData, rate: parseFloat(e.target.value) })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., 18"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">State Code (Optional)</label>
                <input
                  type="text"
                  value={formData.state_code || ''}
                  onChange={(e) => setFormData({ ...formData, state_code: e.target.value })}
                  className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., CA, NY"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Description (Optional)</label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="e.g., Standard GST rate for goods"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => editingId ? handleUpdateRate(editingId) : handleAddRate()}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Saving...' : editingId ? 'Update Rate' : 'Add Rate'}
              </button>
              <button
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Tax Rates List */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead className="bg-gray-100">
              <tr>
                <th className="border border-gray-300 p-3 text-left">Name</th>
                <th className="border border-gray-300 p-3 text-left">Type</th>
                <th className="border border-gray-300 p-3 text-right">Rate (%)</th>
                <th className="border border-gray-300 p-3 text-left">State</th>
                <th className="border border-gray-300 p-3 text-left">Status</th>
                <th className="border border-gray-300 p-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && taxRates.length === 0 ? (
                <tr>
                  <td colSpan={6} className="border border-gray-300 p-3 text-center text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : taxRates.length === 0 ? (
                <tr>
                  <td colSpan={6} className="border border-gray-300 p-3 text-center text-gray-500">
                    No tax rates configured for this region
                  </td>
                </tr>
              ) : (
                taxRates.map(rate => (
                  <tr key={rate.id} className="hover:bg-gray-50">
                    <td className="border border-gray-300 p-3 font-medium">{rate.name}</td>
                    <td className="border border-gray-300 p-3">{rate.tax_type.toUpperCase()}</td>
                    <td className="border border-gray-300 p-3 text-right font-semibold">{rate.rate.toFixed(2)}</td>
                    <td className="border border-gray-300 p-3">{rate.state_code || '-'}</td>
                    <td className="border border-gray-300 p-3">
                      <span className={`px-3 py-1 rounded-full text-sm ${rate.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {rate.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="border border-gray-300 p-3 text-center">
                      <button
                        onClick={() => startEdit(rate)}
                        className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
