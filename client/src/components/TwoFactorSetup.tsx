/**
 * Two-Factor Authentication Setup Component
 */

'use client';

import React, { useState } from 'react';
import Image from 'next/image';

// API call function
const api = {
  post: async (endpoint: string, data: any) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  },
};

interface TwoFactorSetupProps {
  userId: number;
  email: string;
  onComplete?: () => void;
  onCancel?: () => void;
}

interface SetupStep {
  step: 'intro' | 'qr' | 'verify' | 'backup' | 'complete';
}

export function TwoFactorSetup({
  userId,
  email,
  onComplete,
  onCancel,
}: TwoFactorSetupProps) {
  const [setupStep, setSetupStep] = useState<SetupStep['step']>('intro');
  const [qrCode, setQrCode] = useState<string>('');
  const [secret, setSecret] = useState<string>('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  /**
   * Step 1: Generate QR code
   */
  const handleStartSetup = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/v1/auth/2fa/setup', {
        user_id: userId,
      });

      setSecret(response.secret);
      setQrCode(response.qr_code);
      setSetupStep('qr');
    } catch (err: any) {
      setError(err.message || 'Failed to generate QR code');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Step 2: Verify TOTP code
   */
  const handleVerifyCode = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/v1/auth/2fa/verify', {
        user_id: userId,
        token: verificationCode,
      });

      setBackupCodes(response.backup_codes);
      setSetupStep('backup');
    } catch (err: any) {
      setError(err.message || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Copy backup codes to clipboard
   */
  const handleCopyBackupCodes = async () => {
    const text = backupCodes.join('\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('Failed to copy backup codes');
    }
  };

  /**
   * Complete setup
   */
  const handleComplete = () => {
    setSetupStep('complete');
    setTimeout(() => {
      onComplete?.();
    }, 1500);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Intro Step */}
        {setupStep === 'intro' && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Enable Two-Factor Authentication
            </h2>
            <p className="text-gray-600 mb-6">
              Add an extra layer of security to your Vendly account by requiring a code from your phone.
            </p>

            <div className="space-y-3 mb-6 text-sm text-gray-600">
              <div className="flex gap-3">
                <span className="text-blue-600 font-bold">1</span>
                <span>Install an authenticator app (Google Authenticator, Authy, etc.)</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-600 font-bold">2</span>
                <span>Scan the QR code</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-600 font-bold">3</span>
                <span>Enter the 6-digit code to verify</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-600 font-bold">4</span>
                <span>Save your backup codes</span>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={onCancel}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartSetup}
                disabled={loading}
                className="flex-1 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-lg font-medium transition-colors"
              >
                {loading ? 'Loading...' : 'Next'}
              </button>
            </div>
          </>
        )}

        {/* QR Code Step */}
        {setupStep === 'qr' && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Scan QR Code</h2>
            <p className="text-gray-600 mb-4">
              Scan this QR code with your authenticator app:
            </p>

            {qrCode && (
              <div className="flex justify-center mb-6 p-4 bg-gray-50 rounded-lg">
                <Image
                  src={qrCode}
                  alt="2FA QR Code"
                  width={200}
                  height={200}
                />
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <p className="text-sm text-gray-600 mb-6">
              Can&apos;t scan? Enter this code manually:
            </p>
            <div className="bg-gray-100 p-3 rounded-lg font-mono text-sm text-center mb-6 break-all">
              {secret}
            </div>

            <button
              onClick={() => setSetupStep('verify')}
              className="w-full px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
            >
              Next: Verify Code
            </button>
          </>
        )}

        {/* Verify Step */}
        {setupStep === 'verify' && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verify Code</h2>
            <p className="text-gray-600 mb-4">
              Enter the 6-digit code from your authenticator app:
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <input
              type="text"
              maxLength={6}
              placeholder="000000"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
              className="w-full px-4 py-2 border-2 border-gray-300 rounded-lg text-center text-2xl tracking-widest font-mono mb-6 focus:outline-none focus:border-blue-600"
            />

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setSetupStep('qr');
                  setVerificationCode('');
                  setError('');
                }}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleVerifyCode}
                disabled={loading || verificationCode.length !== 6}
                className="flex-1 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-lg font-medium transition-colors"
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>
            </div>
          </>
        )}

        {/* Backup Codes Step */}
        {setupStep === 'backup' && (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Save Backup Codes</h2>
            <p className="text-gray-600 mb-4">
              Save these backup codes in a safe place. You can use them to access your account if you lose access to your authenticator app.
            </p>

            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-xs text-gray-500 mb-3">
                {backupCodes.length} recovery codes generated
              </p>
              <div className="grid grid-cols-2 gap-2">
                {backupCodes.map((code, index) => (
                  <div
                    key={index}
                    className="px-3 py-2 bg-white border border-gray-200 rounded font-mono text-sm"
                  >
                    {code}
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleCopyBackupCodes}
              className="w-full px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition-colors mb-3"
            >
              {copied ? '✓ Copied!' : 'Copy All Codes'}
            </button>

            <button
              onClick={handleComplete}
              className="w-full px-4 py-2 text-white bg-green-600 hover:bg-green-700 rounded-lg font-medium transition-colors"
            >
              Complete Setup
            </button>
          </>
        )}

        {/* Complete Step */}
        {setupStep === 'complete' && (
          <div className="text-center py-8">
            <div className="mb-4">
              <svg
                className="h-16 w-16 text-green-600 mx-auto animate-pulse"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">
              2FA Enabled!
            </h2>
            <p className="text-gray-600 mt-2">
              Two-factor authentication is now active on your account.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default TwoFactorSetup;
