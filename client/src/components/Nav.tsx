'use client';

// ===========================================
// Vendly POS - Navigation Component
// ===========================================

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth, useRoleCheck } from '@/store/auth';

export default function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, token, clearAuth } = useAuth();
  const { isManager, isAdmin } = useRoleCheck();
  const isAuthenticated = !!token;

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
              href="/pos"
              className={`hover:text-primary-600 ${isActive('/pos') ? 'font-semibold text-primary-600' : ''}`}
            >
              POS
            </Link>

            {isManager && (
              <>
                <Link
                  href="/products"
                  className={`hover:text-primary-600 ${isActive('/products') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Products
                </Link>
                <Link
                  href="/inventory"
                  className={`hover:text-primary-600 ${isActive('/inventory') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Inventory
                </Link>
                <Link
                  href="/reports"
                  className={`hover:text-primary-600 ${isActive('/reports') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Reports
                </Link>
              </>
            )}

            {isAdmin && (
              <>
                <Link
                  href="/customers"
                  className={`hover:text-primary-600 ${isActive('/customers') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Customers
                </Link>
                <Link
                  href="/users"
                  className={`hover:text-primary-600 ${isActive('/users') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Users
                </Link>
                <Link
                  href="/settings"
                  className={`hover:text-primary-600 ${isActive('/settings') ? 'font-semibold text-primary-600' : ''}`}
                >
                  Settings
                </Link>
              </>
            )}
          </div>
        )}

        <div className="ml-auto flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <div className="text-sm text-gray-600 flex items-center gap-2">
                <span>{user?.full_name || user?.email}</span>
                {user?.role && (
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.role === 'admin'
                        ? 'bg-red-100 text-red-800'
                        : user.role === 'manager'
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}
                  >
                    {user.role}
                  </span>
                )}
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
