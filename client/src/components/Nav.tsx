'use client';

// ===========================================
// Vendly POS - Navigation Component (Responsive)
// ===========================================

import { useEffect, useState, useRef } from 'react';
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
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close mobile menu on escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };

    if (mobileMenuOpen) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [mobileMenuOpen]);

  const isAuthenticated = mounted && !!token;

  const getRoleStyles = (role: string) => {
    const roleStyles: Record<string, string> = {
      admin: 'bg-red-100 text-red-800',
      manager: 'bg-purple-100 text-purple-800',
      cashier: 'bg-gray-100 text-gray-800',
    };
    return roleStyles[role] || 'bg-gray-100 text-gray-800';
  };

  const getLinkStyles = (isCurrentPage: boolean) => {
    return `hover:text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded transition-colors py-2 md:py-0 block ${isCurrentPage ? 'font-semibold text-primary-600' : ''}`;
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
      <nav className="max-w-7xl mx-auto px-3 md:px-4 py-3 flex items-center justify-between" aria-label="Main navigation">
        {/* Logo */}
        <Link href="/pos" className="font-bold text-lg md:text-xl whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-1">
          Vendly POS
        </Link>

        {/* Desktop Navigation */}
        {isAuthenticated && (
          <div className="hidden md:flex items-center gap-6 text-sm" role="menubar">
            <Link
              href="/returns"
              className={getLinkStyles(isActive('/returns'))}
              role="menuitem"
              aria-current={isActive('/returns') ? 'page' : undefined}
            >
              Refund/Return
            </Link>
            <Link
              href="/pos"
              className={getLinkStyles(isActive('/pos'))}
              role="menuitem"
              aria-current={isActive('/pos') ? 'page' : undefined}
            >
              POS
            </Link>

            {isManager && (
              <>
                <Link
                  href="/products"
                  className={getLinkStyles(isActive('/products'))}
                  role="menuitem"
                  aria-current={isActive('/products') ? 'page' : undefined}
                >
                  Products
                </Link>
                <Link
                  href="/inventory"
                  className={getLinkStyles(isActive('/inventory'))}
                  role="menuitem"
                  aria-current={isActive('/inventory') ? 'page' : undefined}
                >
                  Inventory
                </Link>
                <Link
                  href="/purchase-orders"
                  className={getLinkStyles(isActive('/purchase-orders'))}
                  role="menuitem"
                  aria-current={isActive('/purchase-orders') ? 'page' : undefined}
                >
                  Purchase Orders
                </Link>
                <Link
                  href="/settings/discounts"
                  className={getLinkStyles(isActive('/settings/discounts'))}
                  role="menuitem"
                  aria-current={isActive('/settings/discounts') ? 'page' : undefined}
                >
                  Discounts
                </Link>
                <Link
                  href="/reports"
                  className={getLinkStyles(isActive('/reports'))}
                  role="menuitem"
                  aria-current={isActive('/reports') ? 'page' : undefined}
                >
                  Reports
                </Link>
                <Link
                  href="/forecasts"
                  className={getLinkStyles(isActive('/forecasts'))}
                  role="menuitem"
                  aria-current={isActive('/forecasts') ? 'page' : undefined}
                >
                  Forecasts
                </Link>
                <Link
                  href="/settings"
                  className={getLinkStyles(isActive('/settings'))}
                  role="menuitem"
                  aria-current={isActive('/settings') ? 'page' : undefined}
                >
                  Settings
                </Link>
              </>
            )}

            {isAdmin && (
              <>
                <Link
                  href="/customers"
                  className={getLinkStyles(isActive('/customers'))}
                  role="menuitem"
                  aria-current={isActive('/customers') ? 'page' : undefined}
                >
                  Customers
                </Link>
                <Link
                  href="/users"
                  className={getLinkStyles(isActive('/users'))}
                  role="menuitem"
                  aria-current={isActive('/users') ? 'page' : undefined}
                >
                  Users
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
                      aria-label={`User role: ${user.role}`}
                    >
                      {user.role}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded underline px-1"
                aria-label="Logout"
              >
                Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-1">
              Login
            </Link>
          )}
        </div>

        {/* Mobile Menu Button */}
        {isAuthenticated && (
          <button
            ref={menuButtonRef}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden flex items-center justify-center w-10 h-10 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-menu"
          >
            <svg
              className={`w-6 h-6 transition-transform ${mobileMenuOpen ? 'rotate-90' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}

        {/* Mobile User Menu */}
        {!mounted ? null : !isAuthenticated ? (
          <Link href="/login" className="md:hidden text-sm hover:underline focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-1">
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
        <div
          ref={menuRef}
          className="md:hidden bg-gray-50 border-t border-gray-200 py-3 px-3"
          id="mobile-menu"
          role="menu"
        >
          <div className="space-y-1">
            <Link
              href="/returns"
              onClick={closeMobileMenu}
              className={`block px-3 ${getLinkStyles(isActive('/returns'))}`}
              role="menuitem"
              aria-current={isActive('/returns') ? 'page' : undefined}
            >
              Refund/Return
            </Link>
            <Link
              href="/pos"
              onClick={closeMobileMenu}
              className={`block px-3 ${getLinkStyles(isActive('/pos'))}`}
              role="menuitem"
              aria-current={isActive('/pos') ? 'page' : undefined}
            >
              POS
            </Link>

            {isManager && (
              <>
                <Link
                  href="/products"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/products'))}`}
                  role="menuitem"
                  aria-current={isActive('/products') ? 'page' : undefined}
                >
                  Products
                </Link>
                <Link
                  href="/inventory"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/inventory'))}`}
                  role="menuitem"
                  aria-current={isActive('/inventory') ? 'page' : undefined}
                >
                  Inventory
                </Link>
                <Link
                  href="/settings/discounts"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/settings/discounts'))}`}
                  role="menuitem"
                  aria-current={isActive('/settings/discounts') ? 'page' : undefined}
                >
                  Discounts
                </Link>
                <Link
                  href="/reports"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/reports'))}`}
                  role="menuitem"
                  aria-current={isActive('/reports') ? 'page' : undefined}
                >
                  Reports
                </Link>
                <Link
                  href="/forecasts"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/forecasts'))}`}
                  role="menuitem"
                  aria-current={isActive('/forecasts') ? 'page' : undefined}
                >
                  Forecasts
                </Link>
                <Link
                  href="/settings"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/settings'))}`}
                  role="menuitem"
                  aria-current={isActive('/settings') ? 'page' : undefined}
                >
                  Settings
                </Link>
              </>
            )}

            {isAdmin && (
              <>
                <Link
                  href="/customers"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/customers'))}`}
                  role="menuitem"
                  aria-current={isActive('/customers') ? 'page' : undefined}
                >
                  Customers
                </Link>
                <Link
                  href="/users"
                  onClick={closeMobileMenu}
                  className={`block px-3 ${getLinkStyles(isActive('/users'))}`}
                  role="menuitem"
                  aria-current={isActive('/users') ? 'page' : undefined}
                >
                  Users
                </Link>
              </>
            )}

            <hr className="my-2" />

            <div className="px-3 py-2">
              <p className="text-sm text-gray-600 mb-1">{user?.full_name || user?.email}</p>
              {user?.role && (
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${getRoleStyles(user.role)}`} aria-label={`User role: ${user.role}`}>
                  {user.role}
                </span>
              )}
            </div>

            <button
              onClick={handleLogout}
              className="block w-full text-left text-sm text-red-600 hover:text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 px-3 py-2 rounded"
              role="menuitem"
              aria-label="Logout"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
