// ===========================================
// Vendly POS - Auth Store (Zustand)
// ===========================================

import { create } from 'zustand';

export type UserRole = 'clerk' | 'cashier' | 'manager' | 'admin';

export interface User {
  email: string;
  role: UserRole;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setUser: (user: User | null) => void;
  setToken: (token: string) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
  hasRole: (roles: UserRole[]) => boolean;
}

// No persist - session will be cleared on page refresh
export const useAuth = create<AuthState>()((set, get) => ({
  user: null,
  token: null,

  setUser: (user) => set({ user }),

  setToken: (token) => {
    // Also save to localStorage for API client (during current session)
    if (typeof window !== 'undefined') {
      localStorage.setItem('vendly_token', token);
    }
    set({ token });
  },

  clearAuth: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('vendly_token');
    }
    set({ user: null, token: null });
  },

  isAuthenticated: () => !!get().token,

  hasRole: (roles) => {
    const user = get().user;
    if (!user) return false;
    return roles.includes(user.role);
  },
}));

// Helper hook for role checks
export function useRoleCheck() {
  const { user, hasRole } = useAuth();

  return {
    isAdmin: user?.role === 'admin',
    isManager: user?.role === 'manager' || user?.role === 'admin',
    isCashier: hasRole(['clerk', 'cashier', 'manager', 'admin']),
    canManageProducts: hasRole(['manager', 'admin']),
    canViewReports: hasRole(['manager', 'admin']),
    canManageUsers: user?.role === 'admin',
  };
}
