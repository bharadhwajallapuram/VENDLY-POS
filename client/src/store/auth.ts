// ===========================================
// Vendly POS - Auth Store (Zustand)
// ===========================================

import { create } from 'zustand';

export type UserRole = 'clerk' | 'cashier' | 'manager' | 'admin';

export enum Permission {
  // Sales & POS
  PROCESS_SALES = 'process_sales',
  VOID_SALES = 'void_sales',
  REFUND_SALES = 'refund_sales',
  PROCESS_PAYMENTS = 'process_payments',
  
  // Products
  VIEW_PRODUCTS = 'view_products',
  CREATE_PRODUCTS = 'create_products',
  UPDATE_PRODUCTS = 'update_products',
  DELETE_PRODUCTS = 'delete_products',
  MANAGE_INVENTORY = 'manage_inventory',
  
  // Categories
  MANAGE_CATEGORIES = 'manage_categories',
  
  // Discounts & Coupons
  VIEW_DISCOUNTS = 'view_discounts',
  CREATE_DISCOUNTS = 'create_discounts',
  UPDATE_DISCOUNTS = 'update_discounts',
  DELETE_DISCOUNTS = 'delete_discounts',
  APPLY_DISCOUNTS = 'apply_discounts',
  
  // Customers
  VIEW_CUSTOMERS = 'view_customers',
  CREATE_CUSTOMERS = 'create_customers',
  UPDATE_CUSTOMERS = 'update_customers',
  DELETE_CUSTOMERS = 'delete_customers',
  MANAGE_LOYALTY = 'manage_loyalty',
  
  // Users & Roles
  VIEW_USERS = 'view_users',
  CREATE_USERS = 'create_users',
  UPDATE_USERS = 'update_users',
  DELETE_USERS = 'delete_users',
  MANAGE_ROLES = 'manage_roles',
  
  // Reports & Analytics
  VIEW_REPORTS = 'view_reports',
  VIEW_SALES_REPORTS = 'view_sales_reports',
  VIEW_INVENTORY_REPORTS = 'view_inventory_reports',
  VIEW_CUSTOMER_REPORTS = 'view_customer_reports',
  EXPORT_REPORTS = 'export_reports',
  
  // Settings
  MANAGE_SETTINGS = 'manage_settings',
  MANAGE_PAYMENT_METHODS = 'manage_payment_methods',
  
  // Audit & Compliance
  VIEW_AUDIT_LOG = 'view_audit_log',
}

// Role to permissions mapping
const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  clerk: [
    Permission.PROCESS_SALES,
    Permission.PROCESS_PAYMENTS,
    Permission.REFUND_SALES,
    Permission.VIEW_PRODUCTS,
    Permission.APPLY_DISCOUNTS,
    Permission.VIEW_CUSTOMERS,
    Permission.CREATE_CUSTOMERS,
    Permission.UPDATE_CUSTOMERS,
    Permission.VIEW_SALES_REPORTS,
  ],
  cashier: [
    Permission.PROCESS_SALES,
    Permission.PROCESS_PAYMENTS,
    Permission.REFUND_SALES,
    Permission.VIEW_PRODUCTS,
    Permission.APPLY_DISCOUNTS,
    Permission.VIEW_CUSTOMERS,
    Permission.CREATE_CUSTOMERS,
    Permission.UPDATE_CUSTOMERS,
    Permission.VIEW_SALES_REPORTS,
  ],
  manager: [
    // All cashier permissions
    Permission.PROCESS_SALES,
    Permission.PROCESS_PAYMENTS,
    Permission.REFUND_SALES,
    Permission.VIEW_PRODUCTS,
    Permission.APPLY_DISCOUNTS,
    Permission.VIEW_CUSTOMERS,
    Permission.CREATE_CUSTOMERS,
    Permission.UPDATE_CUSTOMERS,
    Permission.VIEW_SALES_REPORTS,
    
    // Manager-specific
    Permission.VOID_SALES,
    Permission.CREATE_PRODUCTS,
    Permission.UPDATE_PRODUCTS,
    Permission.MANAGE_INVENTORY,
    Permission.MANAGE_CATEGORIES,
    Permission.VIEW_DISCOUNTS,
    Permission.CREATE_DISCOUNTS,
    Permission.UPDATE_DISCOUNTS,
    Permission.DELETE_CUSTOMERS,
    Permission.MANAGE_LOYALTY,
    Permission.VIEW_INVENTORY_REPORTS,
    Permission.VIEW_CUSTOMER_REPORTS,
    Permission.EXPORT_REPORTS,
    Permission.MANAGE_PAYMENT_METHODS,
    Permission.VIEW_AUDIT_LOG,
  ],
  admin: [
    // All manager permissions + admin-only
    Permission.PROCESS_SALES,
    Permission.VOID_SALES,
    Permission.PROCESS_PAYMENTS,
    Permission.REFUND_SALES,
    Permission.VIEW_PRODUCTS,
    Permission.CREATE_PRODUCTS,
    Permission.UPDATE_PRODUCTS,
    Permission.DELETE_PRODUCTS,
    Permission.MANAGE_INVENTORY,
    Permission.MANAGE_CATEGORIES,
    Permission.VIEW_DISCOUNTS,
    Permission.CREATE_DISCOUNTS,
    Permission.UPDATE_DISCOUNTS,
    Permission.DELETE_DISCOUNTS,
    Permission.APPLY_DISCOUNTS,
    Permission.VIEW_CUSTOMERS,
    Permission.CREATE_CUSTOMERS,
    Permission.UPDATE_CUSTOMERS,
    Permission.DELETE_CUSTOMERS,
    Permission.MANAGE_LOYALTY,
    Permission.VIEW_USERS,
    Permission.CREATE_USERS,
    Permission.UPDATE_USERS,
    Permission.DELETE_USERS,
    Permission.MANAGE_ROLES,
    Permission.VIEW_REPORTS,
    Permission.VIEW_SALES_REPORTS,
    Permission.VIEW_INVENTORY_REPORTS,
    Permission.VIEW_CUSTOMER_REPORTS,
    Permission.EXPORT_REPORTS,
    Permission.MANAGE_SETTINGS,
    Permission.MANAGE_PAYMENT_METHODS,
    Permission.VIEW_AUDIT_LOG,
  ],
};

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
  hasPermission: (permission: Permission | Permission[]) => boolean;
  hasAllPermissions: (permissions: Permission[]) => boolean;
  initFromStorage: () => void;
}

// Rehydrate token from localStorage on initialization
const getInitialToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('vendly_token');
  }
  return null;
};

export const useAuth = create<AuthState>()((set, get) => ({
  user: null,
  token: getInitialToken(),

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

  hasPermission: (permission) => {
    const user = get().user;
    if (!user) return false;
    
    const permissions = Array.isArray(permission) ? permission : [permission];
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    
    // Check if user has at least one of the required permissions
    return permissions.some((p) => userPermissions.includes(p));
  },

  hasAllPermissions: (permissions) => {
    const user = get().user;
    if (!user) return false;
    
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    
    // Check if user has all required permissions
    return permissions.every((p) => userPermissions.includes(p));
  },

  initFromStorage: () => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('vendly_token');
      if (token) {
        set({ token });
      }
    }
  },
}));

// Helper hook for role and permission checks
export function useRoleCheck() {
  const { user, hasRole, hasPermission, hasAllPermissions } = useAuth();

  return {
    isAdmin: user?.role === 'admin',
    isManager: user?.role === 'manager' || user?.role === 'admin',
    isCashier: hasRole(['clerk', 'cashier', 'manager', 'admin']),
    
    // Permission checks
    canProcessSales: hasPermission(Permission.PROCESS_SALES),
    canVoidSales: hasPermission(Permission.VOID_SALES),
    canRefundSales: hasPermission(Permission.REFUND_SALES),
    canProcessPayments: hasPermission(Permission.PROCESS_PAYMENTS),
    
    // Product permissions
    canViewProducts: hasPermission(Permission.VIEW_PRODUCTS),
    canCreateProducts: hasPermission(Permission.CREATE_PRODUCTS),
    canUpdateProducts: hasPermission(Permission.UPDATE_PRODUCTS),
    canDeleteProducts: hasPermission(Permission.DELETE_PRODUCTS),
    canManageInventory: hasPermission(Permission.MANAGE_INVENTORY),
    
    // Discount permissions
    canApplyDiscounts: hasPermission(Permission.APPLY_DISCOUNTS),
    canManageDiscounts: hasPermission([Permission.CREATE_DISCOUNTS, Permission.UPDATE_DISCOUNTS]),
    
    // Customer permissions
    canViewCustomers: hasPermission(Permission.VIEW_CUSTOMERS),
    canManageCustomers: hasPermission([Permission.CREATE_CUSTOMERS, Permission.UPDATE_CUSTOMERS]),
    canDeleteCustomers: hasPermission(Permission.DELETE_CUSTOMERS),
    
    // User permissions
    canManageUsers: hasPermission(Permission.MANAGE_ROLES),
    
    // Report permissions
    canViewReports: hasPermission(Permission.VIEW_REPORTS),
    canExportReports: hasPermission(Permission.EXPORT_REPORTS),
  };
}
