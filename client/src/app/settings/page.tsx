'use client';

// ===========================================
// Vendly POS - Settings Page
// ===========================================

import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/store/auth';

function SettingsContent() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Store Settings */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Store Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Store Name
              </label>
              <input className="input" defaultValue="Vendly Store" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency
              </label>
              <select className="input">
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tax Rate (%)
              </label>
              <input className="input" type="number" defaultValue="0" />
            </div>
            <button className="btn btn-primary">Save Store Settings</button>
          </div>
        </div>

        {/* User Profile */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Your Profile</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input className="input" defaultValue={user?.email} disabled />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input className="input" defaultValue={user?.full_name || ''} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Role
              </label>
              <input className="input" defaultValue={user?.role} disabled />
            </div>
            <button className="btn btn-primary">Update Profile</button>
          </div>
        </div>

        {/* User Management (Admin only) */}
        <div className="card md:col-span-2">
          <h2 className="text-lg font-semibold mb-4">User Management</h2>
          <p className="text-gray-500 text-center py-8">
            User management coming soon...
          </p>
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute roles={['admin']}>
      <SettingsContent />
    </ProtectedRoute>
  );
}
