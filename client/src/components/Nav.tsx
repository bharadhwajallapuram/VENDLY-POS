'use client';

// ===========================================
// Vendly POS - Navigation Component
// ===========================================

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth, useRoleCheck } from '@/store/auth';
import OfflineIndicator from './OfflineIndicator';

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, token, clearAuth } = useAuth();
  const { isManager, isAdmin } = useRoleCheck();
  
  // Prevent hydration mismatch by only rendering auth-dependent content after mount
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const isAuthenticated = mounted && !!token;

  const getRoleStyles = (role: string) => {
    const roleStyles: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      manager: 'bg-purple-100 text-purple-800',
      cashier: 'bg-blue-100 text-blue-800',
    };
    return roleStyles[role] || 'bg-gray-100 text-gray-800';
  };

  const getLinkStyles = (isCurrentPage: boolean) => {
    return `hover:text-primary-600 ${isCurrentPage ? 'font-semibold text-primary-600' : ''}`;
  };

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  const isActive = (path: string) => pathname === path;

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
        <Link href="/pos" className="font-bold text-xl">
          Vendly POS
        </Link>

        {isAuthenticated && (
          <div className="flex items-center gap-4 text-sm">
            <Link
              href="/returns"
              className={getLinkStyles(isActive('/returns'))}
            >
              Refund/Return
            </Link>
            <Link
              href="/pos"
              className={getLinkStyles(isActive('/pos'))}
            >
              POS
            </Link>

            {isManager && (
              <>
                <Link
                  href="/products"
                  className={getLinkStyles(isActive('/products'))}
                >
                  Products
                </Link>
                <Link
                  href="/inventory"
                  className={getLinkStyles(isActive('/inventory'))}
                >
                  Inventory
                </Link>
                <Link
                  href="/settings/discounts"
                  className={getLinkStyles(isActive('/settings/discounts'))}
                >
                  Discounts
                </Link>
                <Link
                  href="/reports"
                  className={getLinkStyles(isActive('/reports'))}
                >
                  Reports
                </Link>
              </>
            )}

            {isAdmin && (
              <>
                <Link
                  href="/customers"
                  className={getLinkStyles(isActive('/customers'))}
                >
                  Customers
                </Link>
                <Link
                  href="/users"
                  className={getLinkStyles(isActive('/users'))}
                >
                  Users
                </Link>
                <Link
                  href="/settings"
                  className={getLinkStyles(isActive('/settings'))}
                >
                  Settings
                </Link>
              </>
            )}
          </div>
        )}

        <div className="ml-auto flex items-center gap-3">
          {!mounted ? (
            <div className="text-sm text-gray-400">Loading...</div>
          ) : isAuthenticated ? (
            <>
              <div className="text-sm text-gray-600 flex items-center gap-2">
                <span>{user?.full_name || user?.email}</span>
                <div className="flex items-center gap-1">
                  <OfflineIndicator showDetails={false} />
                  {user?.role && (
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleStyles(user.role)}`}
                    >
                      {user.role}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-600 hover:text-gray-900 underline"
              >
                Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="text-sm hover:underline">
              Login
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}
