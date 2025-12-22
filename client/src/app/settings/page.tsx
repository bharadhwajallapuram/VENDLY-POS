'use client';

// ===========================================
// Vendly POS - Settings Page
// ===========================================

import { useState, useEffect, useCallback } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { TwoFactorSetup } from '@/components/TwoFactorSetup';
import { useAuth } from '@/store/auth';
import { apiFetch } from '@/lib/api';

function SettingsContent() {
  const { user } = useAuth();
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [twoFAStatus, setTwoFAStatus] = useState<{
    enabled: boolean;
    enabled_at?: string;
    backup_codes_remaining?: number;
  } | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);

  const fetchTwoFAStatus = useCallback(async () => {
    try {
      setLoadingStatus(true);
      const status = await apiFetch<typeof twoFAStatus>('/api/v1/auth/2fa/status');
      setTwoFAStatus(status);
    } catch (err) {
      console.error('Failed to fetch 2FA status:', err);
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  useEffect(() => {
    fetchTwoFAStatus();
  }, [fetchTwoFAStatus]);

  const handle2FASuccess = async () => {
    setShow2FASetup(false);
    alert('2FA enabled successfully!');
    await fetchTwoFAStatus();
  };

  const handleDisable2FA = async () => {
    if (!confirm('Are you sure you want to disable 2FA? Your account will be less secure.')) {
      return;
    }

    try {
      await apiFetch('/api/v1/auth/2fa/disable', { method: 'POST' });
      alert('2FA disabled successfully');
      await fetchTwoFAStatus();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to disable 2FA');
    }
  };

  const handleRegenerateBackupCodes = async () => {
    try {
      const response = await apiFetch<{ backup_codes: string[] }>('/api/v1/auth/2fa/regenerate-backup-codes', {
        method: 'POST',
      });
      alert('Backup codes regenerated successfully. Make sure to save them!');
      await fetchTwoFAStatus();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to regenerate backup codes');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {show2FASetup && user ? (
        <div className="card">
          <button
            onClick={() => setShow2FASetup(false)}
            className="text-sm text-gray-600 hover:text-gray-800 mb-4"
          >
            ← Back to Settings
          </button>
          <TwoFactorSetup
            userId={user.id}
            email={user.email}
            onComplete={() => {
              handle2FASuccess();
            }}
            onCancel={() => setShow2FASetup(false)}
          />
        </div>
      ) : (
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

          {/* Security Settings */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">🔒 Security</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Two-Factor Authentication (2FA)
                </label>
                <p className="text-sm text-gray-600 mb-4">
                  Secure your account with TOTP-based 2FA using authenticator apps like Google Authenticator or Authy.
                </p>
                
                {loadingStatus ? (
                  <p className="text-sm text-gray-500">Loading 2FA status...</p>
                ) : twoFAStatus?.enabled ? (
                  <div>
                    <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-800">
                        ✓ <strong>2FA is enabled</strong>
                      </p>
                      {twoFAStatus.backup_codes_remaining && (
                        <p className="text-sm text-green-700 mt-1">
                          {twoFAStatus.backup_codes_remaining} backup codes remaining
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={handleRegenerateBackupCodes}
                        className="btn btn-secondary text-sm"
                      >
                        Regenerate Backup Codes
                      </button>
                      <button
                        onClick={handleDisable2FA}
                        className="btn btn-danger text-sm"
                      >
                        Disable 2FA
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setShow2FASetup(true)}
                    className="btn btn-primary"
                  >
                    Enable 2FA
                  </button>
                )}
              </div>
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
      )}
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute roles={['admin', 'manager']}>
      <SettingsContent />
    </ProtectedRoute>
  );
}
