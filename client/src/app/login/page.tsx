'use client';

// ===========================================
// Vendly POS - Login Page
// ===========================================

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { login, me } from '@/lib/api';
import { useAuth, UserRole } from '@/store/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [tempToken, setTempToken] = useState('');
  const [userEmail, setUserEmail] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login(email, password);

      // Check if 2FA is required
      if (response.requires_2fa) {
        setRequires2FA(true);
        setTempToken(response.temp_token || '');
        setUserEmail(response.email || '');
        setPassword(''); // Clear password for security
        return;
      }

      // No 2FA, login successful
      if (response.access_token) {
        setToken(response.access_token);

        // Fetch user information
        const userInfo = await me();
        setUser({
          id: userInfo.id,
          email: userInfo.email,
          role: userInfo.role as UserRole,
          full_name: userInfo.full_name,
        });

        router.push('/pos');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify2FA(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Determine which code to use
      const code = twoFactorCode || backupCode;
      if (!code) {
        setError('Please enter a 2FA code or backup code');
        setLoading(false);
        return;
      }

      const verify2FAResponse = await fetch(`${API_URL}/api/v1/auth/verify-2fa`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          temp_token: tempToken,
          token: twoFactorCode || '',
          backup_code: backupCode || '',
        }),
      });

      if (!verify2FAResponse.ok) {
        const error = await verify2FAResponse.json();
        throw new Error(error.detail || '2FA verification failed');
      }

      const tokenResponse = await verify2FAResponse.json();
      setToken(tokenResponse.access_token);

      // Fetch user information
      const userInfo = await me();
      setUser({
        id: userInfo.id,
        email: userInfo.email,
        role: userInfo.role as UserRole,
        full_name: userInfo.full_name,
      });

      router.push('/pos');
    } catch (err) {
      setError(err instanceof Error ? err.message : '2FA verification failed');
    } finally {
      setLoading(false);
    }
  }

  // 2FA verification screen
  if (requires2FA) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="w-full max-w-md">
          <div className="card">
            <h1 className="text-2xl font-bold text-center mb-2">Two-Factor Authentication</h1>
            <p className="text-gray-600 text-center mb-6">
              Enter the 6-digit code from your authenticator app
            </p>

            <form onSubmit={handleVerify2FA} className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-2">Signing in as: {userEmail}</p>
              </div>

              <div>
                <label htmlFor="2fa-code" className="block text-sm font-medium text-gray-700 mb-1">
                  Authenticator Code
                </label>
                <input
                  id="2fa-code"
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={twoFactorCode}
                  onChange={(e) => {
                    setTwoFactorCode(e.target.value.replace(/\D/g, ''));
                    setBackupCode('');
                  }}
                  className="input text-center text-2xl tracking-widest font-mono"
                />
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">Or</span>
                </div>
              </div>

              <div>
                <label htmlFor="backup-code" className="block text-sm font-medium text-gray-700 mb-1">
                  Backup Code
                </label>
                <input
                  id="backup-code"
                  type="text"
                  placeholder="XXXX-XXXX-XXXX"
                  value={backupCode}
                  onChange={(e) => {
                    setBackupCode(e.target.value.toUpperCase());
                    setTwoFactorCode('');
                  }}
                  className="input font-mono"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || (!twoFactorCode && !backupCode)}
                className="btn btn-primary w-full"
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>

              <button
                type="button"
                onClick={() => {
                  setRequires2FA(false);
                  setTempToken('');
                  setTwoFactorCode('');
                  setBackupCode('');
                  setError('');
                  setEmail('');
                }}
                className="btn btn-secondary w-full"
              >
                Back to Login
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // Regular login screen
  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="card">
          <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="Enter your email"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-primary-600 hover:underline">
              Register
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
