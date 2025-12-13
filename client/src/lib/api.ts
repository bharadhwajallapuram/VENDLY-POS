// ===========================================
// Vendly POS - API Client
// ===========================================

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to get auth token
function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('vendly_token');
}

// Base fetch wrapper with auth
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle 204 No Content or empty responses
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return undefined as T;
  }

  // Try to parse JSON, return undefined if empty
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  
  return JSON.parse(text);
}

// ===========================================
// Auth API
// ===========================================

export interface LoginResponse {
  access_token?: string;
  token_type?: string;
  requires_2fa?: boolean;
  temp_token?: string;
  user_id?: number;
  email?: string;
}

export interface UserInfo {
  id: number;
  email: string;
  role: string;
  full_name?: string;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

export async function register(email: string, password: string, fullName?: string): Promise<UserInfo> {
  return apiFetch('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
}

export async function me(): Promise<UserInfo> {
  return apiFetch('/api/v1/auth/me');
}

// ===========================================
// Products API
// ===========================================

export interface ProductOut {
  id: number;
  name: string;
  sku?: string;
  barcode?: string;
  description?: string;
  price: number;
  cost?: number;
  quantity: number;
  min_quantity: number;
  category_id?: number;
  tax_rate: number;
  image_url?: string;
  is_active: boolean;
}

export interface ProductIn {
  name: string;
  sku?: string;
  barcode?: string;
  description?: string;
  price: number;
  cost?: number;
  quantity?: number;
  min_quantity?: number;
  category_id?: number;
  tax_rate?: number;
  image_url?: string;
  is_active?: boolean;
}

export const Products = {
  list: (query?: string): Promise<ProductOut[]> => {
    const params = query ? `?q=${encodeURIComponent(query)}` : '';
    return apiFetch(`/api/v1/products${params}`);
  },

  get: (id: number): Promise<ProductOut> => {
    return apiFetch(`/api/v1/products/${id}`);
  },

  create: (data: ProductIn): Promise<ProductOut> => {
    return apiFetch('/api/v1/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: Partial<ProductIn>): Promise<ProductOut> => {
    return apiFetch(`/api/v1/products/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  del: (id: number): Promise<void> => {
    return apiFetch(`/api/v1/products/${id}`, { method: 'DELETE' });
  },
};

// ===========================================
// Sales API
// ===========================================

export interface SaleOut {
  id: string;
  status: string;
  subtotal_cents: number;
  tax_cents: number;
  total_cents: number;
  created_at: string;
}

export interface SaleLineIn {
  variant_id: string;
  qty: number;
  unit_price_cents: number;
}

export interface PaymentIn {
  method_code: string;
  amount_cents: number;
}

export const Sales = {
  open: (storeId: string, registerId: string): Promise<SaleOut> => {
    return apiFetch('/api/v1/sales', {
      method: 'POST',
      body: JSON.stringify({ store_id: storeId, register_id: registerId }),
    });
  },

  get: (id: string): Promise<SaleOut> => {
    return apiFetch(`/api/v1/sales/${id}`);
  },

  addLine: (saleId: string, line: SaleLineIn): Promise<void> => {
    return apiFetch(`/api/v1/sales/${saleId}/lines`, {
      method: 'POST',
      body: JSON.stringify(line),
    });
  },

  addPayment: (saleId: string, payment: PaymentIn): Promise<void> => {
    return apiFetch(`/api/v1/sales/${saleId}/payments`, {
      method: 'POST',
      body: JSON.stringify(payment),
    });
  },

  complete: (saleId: string): Promise<SaleOut> => {
    return apiFetch(`/api/v1/sales/${saleId}/complete`, {
      method: 'POST',
    });
  },

  void: (saleId: string): Promise<void> => {
    return apiFetch(`/api/v1/sales/${saleId}/void`, {
      method: 'POST',
    });
  },
};

// ===========================================
// Reports API
// ===========================================

export interface ReportSummary {
  total_sales: number;
  total_revenue: number;
  average_sale: number;
  top_products: { name: string; quantity: number; revenue: number }[];
  // Refund/Return statistics
  total_refunds?: number;
  total_returns?: number;
  refund_amount?: number;
  return_amount?: number;
}

export const Reports = {
  summary: (startDate?: string, endDate?: string): Promise<ReportSummary> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const query = params.toString() ? `?${params}` : '';
    return apiFetch(`/api/v1/reports/summary${query}`);
  },

  sales: (startDate?: string, endDate?: string): Promise<SaleOut[]> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const query = params.toString() ? `?${params}` : '';
    return apiFetch(`/api/v1/reports/sales${query}`);
  },

  // End-of-Day Reports
  zReport: (reportDate?: string): Promise<any> => {
    const params = reportDate ? `?report_date=${reportDate}` : '';
    return apiFetch(`/api/v1/reports/z-report${params}`);
  },

  reconcileCash: (actualCash: number, reportDate?: string, notes?: string): Promise<any> => {
    const params = new URLSearchParams();
    if (reportDate) params.append('report_date', reportDate);
    const query = params.toString() ? `?${params}` : '';
    return apiFetch(`/api/v1/reports/z-report/reconcile${query}`, {
      method: 'POST',
      body: JSON.stringify({ actual_cash: actualCash, notes }),
    });
  },

  salesSummary: (reportDate?: string): Promise<any> => {
    const params = reportDate ? `?report_date=${reportDate}` : '';
    return apiFetch(`/api/v1/reports/sales-summary${params}`);
  },
};

// ===========================================
// Customers API
// ===========================================

export interface CustomerOut {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  loyalty_points: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CustomerIn {
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
  loyalty_points?: number;
  is_active?: boolean;
}

export const Customers = {
  list: (query?: string): Promise<CustomerOut[]> => {
    const params = query ? `?q=${encodeURIComponent(query)}` : '';
    return apiFetch(`/api/v1/customers${params}`);
  },

  get: (id: number): Promise<CustomerOut> => {
    return apiFetch(`/api/v1/customers/${id}`);
  },

  create: (data: CustomerIn): Promise<CustomerOut> => {
    return apiFetch('/api/v1/customers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: Partial<CustomerIn>): Promise<CustomerOut> => {
    return apiFetch(`/api/v1/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  del: (id: number): Promise<void> => {
    return apiFetch(`/api/v1/customers/${id}`, { method: 'DELETE' });
  },

  adjustLoyalty: (id: number, points: number, reason?: string): Promise<CustomerOut> => {
    return apiFetch(`/api/v1/customers/${id}/adjust-loyalty`, {
      method: 'POST',
      body: JSON.stringify({ points, reason }),
    });
  },
};

// ===========================================
// Users API (Admin Only)
// ===========================================

export interface UserOut {
  id: number;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
}

export interface UserIn {
  email: string;
  password: string;
  full_name?: string;
  role?: string;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
}

export const Users = {
  list: (query?: string): Promise<UserOut[]> => {
    const params = query ? `?q=${encodeURIComponent(query)}` : '';
    return apiFetch(`/api/v1/users${params}`);
  },

  get: (id: number): Promise<UserOut> => {
    return apiFetch(`/api/v1/users/${id}`);
  },

  create: (data: UserIn): Promise<UserOut> => {
    return apiFetch('/api/v1/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: UserUpdate): Promise<UserOut> => {
    return apiFetch(`/api/v1/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  del: (id: number): Promise<void> => {
    return apiFetch(`/api/v1/users/${id}`, { method: 'DELETE' });
  },
};

// ===========================================
// Coupons API
// ===========================================

export interface CouponOut {
  id: number;
  code: string;
  type: 'percent' | 'amount';
  value: number;
  max_off?: number | null;
  min_order?: number | null;
  active: boolean;
  expires_at?: string | null;
  usage_count: number;
  stackable: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface CouponIn {
  code: string;
  type: 'percent' | 'amount';
  value: number;
  max_off?: number | null;
  min_order?: number | null;
  active?: boolean;
  expires_at?: string | null;
  stackable?: boolean;
}

export interface CouponUpdate {
  code?: string;
  type?: 'percent' | 'amount';
  value?: number;
  max_off?: number | null;
  min_order?: number | null;
  active?: boolean;
  expires_at?: string | null;
  stackable?: boolean;
}

export interface CouponValidateResponse {
  valid: boolean;
  coupon?: CouponOut | null;
  discount_amount: number;
  message: string;
}

export const couponsApi = {
  list: (activeOnly: boolean = false): Promise<CouponOut[]> => {
    return apiFetch(`/api/v1/coupons?active_only=${activeOnly}`);
  },

  get: (id: number): Promise<CouponOut> => {
    return apiFetch(`/api/v1/coupons/${id}`);
  },

  create: (data: CouponIn): Promise<CouponOut> => {
    return apiFetch('/api/v1/coupons', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: CouponUpdate): Promise<CouponOut> => {
    return apiFetch(`/api/v1/coupons/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  del: (id: number): Promise<void> => {
    return apiFetch(`/api/v1/coupons/${id}`, { method: 'DELETE' });
  },

  toggle: (id: number): Promise<CouponOut> => {
    return apiFetch(`/api/v1/coupons/${id}/toggle`, { method: 'PATCH' });
  },

  validate: (code: string, orderTotal: number): Promise<CouponValidateResponse> => {
    return apiFetch('/api/v1/coupons/validate', {
      method: 'POST',
      body: JSON.stringify({ code, order_total: orderTotal }),
    });
  },

  incrementUsage: (id: number): Promise<CouponOut> => {
    return apiFetch(`/api/v1/coupons/${id}/increment-usage`, { method: 'POST' });
  },
};

// ===========================================
// WebSocket
// ===========================================

export function createWebSocket(onMessage: (data: unknown) => void): WebSocket | null {
  if (typeof window === 'undefined') return null;
  
  const wsUrl = API_URL.replace(/^http/, 'ws') + '/api/v1/ws';
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.error('Failed to parse WebSocket message');
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  return ws;
}
