'use client';

// ===========================================
// Vendly POS - Navigation Component (Responsive)
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
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
    return `hover:text-primary-600 transition-colors py-2 md:py-0 block ${isCurrentPage ? 'font-semibold text-primary-600' : ''}`;
  };

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
    setMobileMenuOpen(false);
  };

  const isActive = (path: string) => pathname === path;

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-3 md:px-4 py-3 flex items-center justify-between">
        {/* Logo */}
        <Link href="/pos" className="font-bold text-lg md:text-xl whitespace-nowrap">
          Vendly POS
        </Link>

        {/* Desktop Navigation */}
        {isAuthenticated && (
          <div className="hidden md:flex items-center gap-6 text-sm">
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

        {/* Right Side - Desktop */}
        <div className="hidden md:flex items-center gap-4">
          {!mounted ? (
            <div className="text-sm text-gray-400">Loading...</div>
          ) : isAuthenticated ? (
            <>
              <div className="text-sm text-gray-600 flex items-center gap-2">
                <span className="hidden lg:inline">{user?.full_name || user?.email}</span>
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

        {/* Mobile Menu Button */}
        {isAuthenticated && (
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex items-center justify-center w-10 h-10 text-gray-600 hover:text-gray-900"
            aria-label="Toggle menu"
          >
            <svg
              className={`w-6 h-6 transition-transform ${mobileMenuOpen ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Mobile User Menu */}
        {!mounted ? null : !isAuthenticated ? (
          <Link href="/login" className="md:hidden text-sm hover:underline">
            Login
          </Link>
        ) : (
          <div className="md:hidden flex items-center gap-2">
            <OfflineIndicator showDetails={false} />
          </div>
        )}
      </nav>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && isAuthenticated && (
        <div className="md:hidden bg-gray-50 border-t border-gray-200 py-3 px-3">
          <div className="space-y-1">
            <Link
              href="/returns"
              onClick={closeMobileMenu}
              className={`block px-3 ${getLinkStyles(isActive('/returns'))}`}
            >
              Refund/Return
            </Link>
            <Link
              href="/pos"
              onClick={closeMobileMenu}
              className={`block px-3 ${getLinkStyles(isActive('/pos'))}`}
            >
              POS
            </Link>

            {isManager && (
              <>
                <Link
                  href="/products"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/products'))}`}
                >
                  Products
                </Link>
                <Link
                  href="/inventory"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/inventory'))}`}
                >
                  Inventory
                </Link>
                <Link
                  href="/settings/discounts"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/settings/discounts'))}`}
                >
                  Discounts
                </Link>
                <Link
                  href="/reports"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/reports'))}`}
                >
                  Reports
                </Link>
              </>
            )}

            {isAdmin && (
              <>
                <Link
                  href="/customers"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/customers'))}`}
                >
                  Customers
                </Link>
                <Link
                  href="/users"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/users'))}`}
                >
                  Users
                </Link>
                <Link
                  href="/settings"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/settings'))}`}
                >
                  Settings
                </Link>
              </>
            )}

            <hr className="my-2" />

            <div className="px-3 py-2">
              <p className="text-sm text-gray-600 mb-1">{user?.full_name || user?.email}</p>
              {user?.role && (
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getRoleStyles(user.role)}`}>
                  {user.role}
                </span>
              )}
            </div>

            <button
              onClick={handleLogout}
              className="block w-full text-left text-sm text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
